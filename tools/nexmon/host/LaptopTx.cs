// Bounded MT7922 UDP transmitter. No shell, installation, Wi-Fi changes or CSI synthesis.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Management;
using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;

class LaptopTx
{
    const string Server = "http://192.168.137.1:39032";
    const string LanServer = "http://192.168.50.102:39032";
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = 2000000 };
    static volatile bool Cancel;
    static TextBox Log;
    static Thread Worker;
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern IntPtr CreateWaitableTimerExW(IntPtr attributes, string name, uint flags, uint access);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool SetWaitableTimer(IntPtr timer, ref long due, int period, IntPtr callback, IntPtr argument, bool resume);
    [DllImport("kernel32.dll", SetLastError = true)] static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
    static long Ns(long ticks) { long f = Stopwatch.Frequency; return ticks / f * 1000000000L + ticks % f * 1000000000L / f; }
    static void Show(string value) {
        if (Log != null && !Log.IsDisposed && Log.IsHandleCreated)
            try { Log.BeginInvoke((Action)(() => Log.AppendText(value + Environment.NewLine))); } catch (InvalidOperationException) { }
    }
    static string Http(string origin, string path, object body) {
        var request = (HttpWebRequest)WebRequest.Create(origin + path);
        request.Proxy = null; request.Timeout = 3000; request.ReadWriteTimeout = 3000;
        request.KeepAlive = false;
        if (body != null) {
            byte[] bytes = Encoding.UTF8.GetBytes(Json.Serialize(body));
            request.Method = "POST"; request.ContentType = "application/json"; request.ContentLength = bytes.Length;
            using (var stream = request.GetRequestStream()) stream.Write(bytes, 0, bytes.Length);
        }
        using (var response = request.GetResponse())
        using (var reader = new StreamReader(response.GetResponseStream(), Encoding.UTF8)) return reader.ReadToEnd();
    }
    static Dictionary<string, object> Inventory(bool smoke, bool quick = false) {
        var result = new Dictionary<string, object> {
            {"schema", 1}, {"computer_name", Environment.MachineName}, {"user_name", Environment.UserName},
            {"loopback_only", smoke}, {"stopwatch_frequency", Stopwatch.Frequency}, {"utc", DateTime.UtcNow.ToString("o")}
        };
        var nics = new List<object>();
        foreach (var nic in NetworkInterface.GetAllNetworkInterfaces()) {
            if (nic.NetworkInterfaceType != NetworkInterfaceType.Wireless80211) continue;
            var addresses = new List<string>();
            foreach (var address in nic.GetIPProperties().UnicastAddresses)
                if (address.Address.AddressFamily == AddressFamily.InterNetwork) addresses.Add(address.Address.ToString());
            nics.Add(new { name = nic.Name, description = nic.Description, mac = nic.GetPhysicalAddress().ToString(),
                state = nic.OperationalStatus.ToString(), ipv4 = addresses });
        }
        result["wireless_interfaces"] = nics;
        // A controlled SSH run has already checked OS/driver identity. Avoid
        // potentially slow WMI here, before the bounded transmitter is armed.
        if (quick) { result["driver_inventory"] = "Read by separate SSH preflight"; return result; }
        var drivers = new List<object>();
        try {
            using (var search = new ManagementObjectSearcher("SELECT Caption,Version,BuildNumber FROM Win32_OperatingSystem"))
                foreach (ManagementObject item in search.Get()) result["os"] = new {
                    caption = item["Caption"], version = item["Version"], build = item["BuildNumber"] };
            using (var search = new ManagementObjectSearcher("SELECT DeviceID,DriverVersion,DriverDate,DeviceName FROM Win32_PnPSignedDriver WHERE DeviceName LIKE '%MT7922%'"))
                foreach (ManagementObject item in search.Get()) drivers.Add(new {
                    device_id = item["DeviceID"], version = item["DriverVersion"], date = item["DriverDate"], name = item["DeviceName"] });
            result["drivers"] = drivers;
        } catch (Exception ex) { result["driver_read_error"] = ex.GetType().Name + ": " + ex.Message; }
        return result;
    }
    static double Q(List<double> values, double p) { return values.Count == 0 ? 0 : values[(int)Math.Round((values.Count - 1) * p)]; }
    static object Transmit(Dictionary<string, object> job, bool smoke) {
        int hz = Convert.ToInt32(job["hz"]), seconds = Convert.ToInt32(job["seconds"]);
        string id = (string)job["id"], target = (string)job["destination"];
        Guid.ParseExact(id, "N");
        if ((hz != 50 && hz != 300) || (seconds != 2 && seconds != 10 && seconds != 20)) throw new ArgumentException("Rate/duration budget rejected");
        IPAddress parsedTarget;
        bool phone = IPAddress.TryParse(target, out parsedTarget) && target.StartsWith("172.20.10.") &&
            parsedTarget.GetAddressBytes()[3] >= 1 && parsedTarget.GetAddressBytes()[3] <= 14;
        if (smoke ? target != "127.0.0.1" : (target != "192.168.137.1" && target != "192.168.50.102" && !phone))
            throw new ArgumentException("Destination rejected");
        string subnet = phone ? "172.20.10." : target == "192.168.50.102" ? "192.168.50." : "192.168.137.";
        IPAddress source = smoke ? IPAddress.Loopback : null;
        NetworkInterface selected = null;
        if (!smoke) {
            foreach (var nic in NetworkInterface.GetAllNetworkInterfaces()) {
                if (nic.NetworkInterfaceType != NetworkInterfaceType.Wireless80211 || nic.OperationalStatus != OperationalStatus.Up ||
                    nic.Description.IndexOf("MT7922", StringComparison.OrdinalIgnoreCase) < 0) continue;
                foreach (var address in nic.GetIPProperties().UnicastAddresses)
                    if (address.Address.AddressFamily == AddressFamily.InterNetwork && address.Address.ToString().StartsWith(subnet)) {
                        if (source != null) throw new ArgumentException("Ambiguous MT7922 source");
                        source = address.Address; selected = nic;
                    }
            }
            if (selected == null) throw new ArgumentException("Connected MT7922 on the selected test subnet is required");
        }
        var rows = new List<long[]>();
        int slots = hz * seconds, skipped = 0;
        string error = null;
        bool priority = false;
        IntPtr timer = IntPtr.Zero;
        var process = Process.GetCurrentProcess();
        var previous = process.PriorityClass;
        long begin = 0, elapsed = 0;
        byte[] payload = new byte[256];
        Buffer.BlockCopy(Encoding.ASCII.GetBytes("CSI300V1"), 0, payload, 0, 8);
        for (int i = 0; i < 16; i++) payload[32 + i] = Convert.ToByte(id.Substring(i * 2, 2), 16);
        using (var socket = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp)) {
            socket.SendTimeout = 1000;
            if (selected != null) socket.SetSocketOption(SocketOptionLevel.IP, (SocketOptionName)31,
                IPAddress.HostToNetworkOrder(selected.GetIPProperties().GetIPv4Properties().Index));
            socket.Bind(new IPEndPoint(source, 0));
            var endpoint = new IPEndPoint(IPAddress.Parse(target), 39031);
            try {
                // Sleep() can retain ~15.6 ms granularity in an occluded Windows GUI.
                // Use the explicit high-resolution waitable timer, then QPC for the last 500 us.
                timer = CreateWaitableTimerExW(IntPtr.Zero, null, 2, 0x100002);
                if (timer == IntPtr.Zero) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error(), "High-resolution timer unavailable");
                try { process.PriorityClass = ProcessPriorityClass.AboveNormal; priority = true; } catch (System.ComponentModel.Win32Exception) { }
                long frequency = Stopwatch.Frequency;
                double period = (double)frequency / hz;
                begin = Stopwatch.GetTimestamp() + frequency / 10;
                for (int slot = 0; slot < slots && !Cancel; slot++) {
                    long deadline = begin + (long)Math.Round(slot * period), now;
                    while ((now = Stopwatch.GetTimestamp()) < deadline && !Cancel) {
                        double ms = (deadline - now) * 1000.0 / frequency;
                        if (ms > 1.5) {
                            long timerDue = -(long)(Math.Min(10, ms - 0.5) * 10000);
                            if (!SetWaitableTimer(timer, ref timerDue, 0, IntPtr.Zero, IntPtr.Zero, false))
                                throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
                            uint wait = WaitForSingleObject(timer, 1000);
                            if (wait != 0) throw new InvalidOperationException("Timer wait failed: " + wait);
                        } else Thread.SpinWait(15);
                    }
                    if (Cancel) break;
                    long before = Stopwatch.GetTimestamp();
                    int due = (int)((before - begin) / period);
                    if (due > slot) { skipped += Math.Min(due, slots) - slot; slot = due; if (slot >= slots) break; deadline = begin + (long)Math.Round(slot * period); }
                    Buffer.BlockCopy(BitConverter.GetBytes((ulong)slot), 0, payload, 8, 8);
                    Buffer.BlockCopy(BitConverter.GetBytes((ulong)Ns(before)), 0, payload, 16, 8);
                    Buffer.BlockCopy(BitConverter.GetBytes((ulong)Ns(deadline)), 0, payload, 24, 8);
                    int sent = socket.SendTo(payload, endpoint);
                    long after = Stopwatch.GetTimestamp();
                    rows.Add(new long[] { slot, Ns(deadline), Ns(before), Ns(after), sent });
                }
            } catch (Exception ex) { error = ex.GetType().Name + ": " + ex.Message; }
            finally {
                elapsed = begin == 0 ? 0 : Stopwatch.GetTimestamp() - begin;
                if (priority) process.PriorityClass = previous;
                if (timer != IntPtr.Zero) CloseHandle(timer);
            }
        }
        var intervals = new List<double>(); var latency = new List<double>();
        for (int i = 0; i < rows.Count; i++) {
            latency.Add((rows[i][3] - rows[i][2]) / 1000000.0);
            if (i > 0) intervals.Add((rows[i][2] - rows[i - 1][2]) / 1000000.0);
        }
        intervals.Sort(); latency.Sort();
        double rate = rows.Count > 1 ? (rows.Count - 1) * 1e9 / (rows[rows.Count - 1][2] - rows[0][2]) : 0;
        return new { schema = 1, id = id, computer_name = Environment.MachineName, hardware_test = !smoke,
            source = source.ToString(), destination = target, port = 39031, nic = selected == null ? "loopback" : selected.Description,
            mac = selected == null ? null : selected.GetPhysicalAddress().ToString(), requested_hz = hz, requested_seconds = seconds,
            scheduled_slots = slots, send_calls_succeeded = rows.Count, skipped_late_slots = skipped,
            schedule_complete = rows.Count == slots && skipped == 0 && error == null && !Cancel,
            cancelled = Cancel, error = error, send_call_rate_hz = rate, elapsed_seconds = elapsed * 1.0 / Stopwatch.Frequency,
            timing_tuning = new { high_resolution_waitable_timer = timer != IntPtr.Zero, above_normal = priority },
            interval_ms = new { p50 = Q(intervals, .5), p95 = Q(intervals, .95), p99 = Q(intervals, .99), max = Q(intervals, 1) },
            send_latency_ms = new { p99 = Q(latency, .99), max = Q(latency, 1) },
            columns = new string[] { "slot", "target_ns", "before_send_ns", "after_send_ns", "bytes" }, sends = rows,
            limitation = "Socket send completion and IP delivery are not proof of independent RF frames or CSI sampling" };
    }
    static int Work(string server, bool smoke, bool once = false) {
        var seen = new HashSet<string>(); bool registered = false;
        var inventory = Inventory(smoke, once);
        var deadline = once ? DateTime.UtcNow.AddSeconds(45) : DateTime.UtcNow.AddMinutes(smoke ? 1 : 20);
        while (!Cancel && DateTime.UtcNow < deadline) {
            try {
                if (!registered) { Http(server, "/inventory", inventory); registered = true; Show("已连接控制端；等待有界测试。关闭本窗口即可停止。"); }
                var job = Json.Deserialize<Dictionary<string, object>>(Http(server, "/task", null));
                if (job == null) { Thread.Sleep(500); continue; }
                string id = (string)job["id"];
                if (!seen.Add(id)) throw new InvalidOperationException("Refusing to repeat an assigned experiment");
                Show("开始 " + job["hz"] + " Hz / " + job["seconds"] + " 秒，ID " + id);
                object result;
                try { result = Transmit(job, smoke); }
                catch (Exception ex) { result = new { id = id, error = ex.GetType().Name + ": " + ex.Message, hardware_test = !smoke }; }
                string folder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "NexmonTx");
                Directory.CreateDirectory(folder);
                string file = Path.Combine(folder, id + ".json");
                using (var stream = new StreamWriter(new FileStream(file, FileMode.CreateNew, FileAccess.Write), Encoding.UTF8)) stream.Write(Json.Serialize(result));
                // Keep the result HTTP upload outside the receiver's bounded 16 s CSI window.
                if (!smoke) for (int i = 0; i < 60 && !Cancel; i++) Thread.Sleep(100);
                bool returned = false;
                for (int attempt = 0; attempt < 3 && !returned; attempt++) {
                    try { Http(server, "/result", result); returned = true; }
                    catch (WebException) { if (attempt == 2) throw; Thread.Sleep(500); }
                }
                Show("测试完成，原始台账已保存：" + file);
                if (smoke || once) return 0;
            } catch (Exception ex) { Show(ex.GetType().Name + ": " + ex.Message); if (smoke || once) return 2; Thread.Sleep(1500); }
        }
        return once ? 4 : 0;
    }
    [STAThread] static int Main(string[] args) {
        if (args.Length == 1 && args[0] == "--smoke") return Work("http://127.0.0.1:39032", true);
        if (args.Length == 1 && args[0] == "--once") return Work(Server, false, true);
        if (args.Length == 2 && args[0] == "--once" && args[1] == "--lan") return Work(LanServer, false, true);
        if (args.Length != 0) return 2;
        Application.EnableVisualStyles();
        var form = new Form { Text = "RT-AC86U 临时发射验证 / MT7922", Width = 780, Height = 360 };
        Log = new TextBox { Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Vertical, Dock = DockStyle.Fill };
        form.Controls.Add(Log);
        form.Shown += (s, e) => { Show("仅使用 MT7922 向本机热点发送有界测试数据；不安装服务、不修改无线设置。最长运行20分钟。"); Worker = new Thread(() => Work(Server, false)) { IsBackground = true }; Worker.Start(); };
        bool stopping = false;
        form.FormClosing += (s, e) => {
            Cancel = true;
            if (Worker == null || !Worker.IsAlive) return;
            e.Cancel = true;
            if (stopping) return;
            stopping = true;
            Show("正在停止并保存已发送数据，请稍候。");
            var timer = new System.Windows.Forms.Timer { Interval = 100 };
            timer.Tick += (sender, tick) => { if (!Worker.IsAlive) { timer.Stop(); timer.Dispose(); form.Close(); } };
            timer.Start();
        };
        Application.Run(form); return 0;
    }
}
