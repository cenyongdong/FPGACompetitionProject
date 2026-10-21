// Temporary, explicitly scoped firewall access for the existing Windows SSH service.
using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.NetworkInformation;
using System.Security.Cryptography;
using System.Security.Principal;
using System.ServiceProcess;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;

class LaptopSshAccess
{
    [STAThread] static int Main() {
        Application.EnableVisualStyles();
        var form = new Form { Text = "MT7922 SSH 临时连接 / 关闭后撤销放行", Width = 850, Height = 350 };
        var log = new TextBox { Dock = DockStyle.Fill, Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Vertical };
        form.Controls.Add(log);
        string id = Guid.NewGuid().ToString("N"), ruleName = "Nexmon-Temporary-SSH-" + id;
        string eventName = "Global\\NexmonSshAccess_" + id;
        dynamic policy = null;
        bool added = false;
        bool startedService = false;
        ServiceController sshService = null;
        EventWaitHandle stop = null;
        var deadline = DateTime.UtcNow.AddMinutes(20);
        form.Shown += (s, e) => {
            try {
                if (Environment.MachineName != "DESKTOP-V4Q9HC6") throw new InvalidOperationException("非目标笔记本，未修改设置。");
                var principal = new WindowsPrincipal(WindowsIdentity.GetCurrent());
                if (!principal.IsInRole(WindowsBuiltInRole.Administrator)) throw new InvalidOperationException("需要由你批准管理员权限，才能临时放行端口。");
                bool matched = false, wired = false;
                foreach (var nic in NetworkInterface.GetAllNetworkInterfaces()) {
                    foreach (var ip in nic.GetIPProperties().UnicastAddresses)
                        if (nic.OperationalStatus == OperationalStatus.Up && nic.NetworkInterfaceType == NetworkInterfaceType.Ethernet &&
                            ip.Address.ToString() == "192.168.50.70") wired = true;
                    if (nic.Description.IndexOf("MT7922", StringComparison.OrdinalIgnoreCase) < 0 ||
                        nic.GetPhysicalAddress().ToString() != "50BBB5DBA502") continue;
                    matched = true;
                }
                if (!matched) throw new InvalidOperationException("MT7922 身份已变化，未修改设置。");
                if (!wired) throw new InvalidOperationException("需要当前已确认的有线地址 192.168.50.70；未修改设置。");
                string local = "192.168.50.70", remote = "192.168.50.102";
                sshService = new ServiceController("sshd");
                if (sshService.Status == ServiceControllerStatus.Stopped) {
                    sshService.Start();
                    startedService = true;
                    sshService.WaitForStatus(ServiceControllerStatus.Running, TimeSpan.FromSeconds(10));
                }
                bool listening = false;
                foreach (var endpoint in IPGlobalProperties.GetIPGlobalProperties().GetActiveTcpListeners())
                    if (endpoint.Port == 22 && (endpoint.Address.Equals(IPAddress.Any) || endpoint.Address.Equals(IPAddress.IPv6Any) ||
                        endpoint.Address.ToString() == local)) listening = true;
                if (!listening) throw new InvalidOperationException("SSH 尚未监听热点接口的22端口；请检查 OpenSSH SSH Server 服务，未新增规则。");
                string key = File.ReadAllText(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "ssh", "ssh_host_ed25519_key.pub")).Trim();
                string[] fields = key.Split(new char[] {' ', '\t'}, StringSplitOptions.RemoveEmptyEntries);
                if (fields.Length < 2 || fields[0] != "ssh-ed25519") throw new InvalidOperationException("SSH 公钥格式异常。");
                string fingerprint;
                using (var sha = SHA256.Create()) fingerprint = "SHA256:" + Convert.ToBase64String(sha.ComputeHash(Convert.FromBase64String(fields[1]))).TrimEnd('=');
                stop = new EventWaitHandle(false, EventResetMode.ManualReset, eventName);
                policy = Activator.CreateInstance(Type.GetTypeFromProgID("HNetCfg.FwPolicy2"));
                dynamic rule = Activator.CreateInstance(Type.GetTypeFromProgID("HNetCfg.FWRule"));
                rule.Name = ruleName;
                rule.Description = "Nexmon 单次验证；仅桌面热点主机，窗口关闭或20分钟后撤销。";
                rule.Protocol = 6;
                rule.LocalPorts = "22";
                rule.LocalAddresses = local;
                rule.RemoteAddresses = remote;
                rule.Direction = 1;
                rule.Action = 1;
                rule.Profiles = int.MaxValue;
                rule.Enabled = true;
                policy.Rules.Add(rule);
                added = true;
                var info = new { computer_name = Environment.MachineName, user_name = Environment.UserName,
                    identity = WindowsIdentity.GetCurrent().Name, mac = "50:bb:b5:db:a5:02", ip = local,
                    host_public_key = fields[0] + " " + fields[1], host_fingerprint = fingerprint,
                    rule_name = ruleName, stop_event = eventName, pid = Process.GetCurrentProcess().Id,
                    expires_utc = deadline.ToString("o"), ssh_started_by_helper = startedService };
                var json = new JavaScriptSerializer().Serialize(info);
                string folder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "NexmonTx");
                Directory.CreateDirectory(folder);
                File.WriteAllText(Path.Combine(folder, "ssh-access-" + id + ".json"), json);
                using (var web = new WebClient()) {
                    web.Proxy = null;
                    web.Headers[HttpRequestHeader.ContentType] = "application/json";
                    web.UploadString("http://" + remote + ":39032/access-info", json);
                }
                log.AppendText("临时放行已就绪，仅允许 " + remote + " → " + local + ":22。\r\n");
                log.AppendText("账户：" + info.identity + "\r\nSSH 指纹：" + fingerprint + "\r\n");
                log.AppendText("请保留本窗口，可以最小化；关闭或20分钟后自动撤销规则。\r\n不安装服务、不改变SSH启动类型、不修改无线设置；如果本工具临时启动了SSH，关闭时恢复停止。\r\n");
            } catch (Exception ex) {
                if (added) { try { policy.Rules.Remove(ruleName); added = false; } catch { } }
                if (startedService) { try { sshService.Stop(); startedService = false; } catch { } }
                log.AppendText(ex.GetType().Name + ": " + ex.Message + "\r\n请把此窗口显示的错误告知代理。");
            }
        };
        form.FormClosing += (s, e) => {
            if (added) {
                try { policy.Rules.Remove(ruleName); added = false; }
                catch (Exception ex) { log.AppendText("撤销规则失败：" + ex.Message + "\r\n"); e.Cancel = true; return; }
            }
            if (stop != null) { stop.Dispose(); stop = null; }
            if (startedService) {
                try { sshService.Stop(); startedService = false; }
                catch (Exception ex) { log.AppendText("恢复SSH服务状态失败：" + ex.Message + "\r\n"); e.Cancel = true; return; }
            }
        };
        var timer = new System.Windows.Forms.Timer { Interval = 250 };
        timer.Tick += (s, e) => { if (DateTime.UtcNow >= deadline || (stop != null && stop.WaitOne(0))) form.Close(); };
        timer.Start();
        Application.Run(form);
        timer.Dispose();
        if (sshService != null) sshService.Dispose();
        return added ? 1 : 0;
    }
}
