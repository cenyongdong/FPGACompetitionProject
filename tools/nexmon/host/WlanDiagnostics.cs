// Native WLAN telemetry and bounded, handle-owned scan control. No scan requests.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;

public static class WlanDiagnostics {
    [StructLayout(LayoutKind.Sequential)] struct Notice {
        public uint Source, Code; public Guid Interface; public uint Size; public IntPtr Data;
    }
    delegate void Callback(ref Notice notice, IntPtr context);
    [DllImport("wlanapi.dll")] static extern uint WlanOpenHandle(uint version, IntPtr reserved, out uint negotiated, out IntPtr handle);
    [DllImport("wlanapi.dll")] static extern uint WlanCloseHandle(IntPtr handle, IntPtr reserved);
    [DllImport("wlanapi.dll")] static extern uint WlanQueryInterface(IntPtr handle, ref Guid id, uint opcode, IntPtr reserved, out uint size, out IntPtr data, out uint type);
    [DllImport("wlanapi.dll")] static extern uint WlanSetInterface(IntPtr handle, ref Guid id, uint opcode, uint size, ref int value, IntPtr reserved);
    [DllImport("wlanapi.dll")] static extern uint WlanRegisterNotification(IntPtr handle, uint source, bool ignore, Callback callback, IntPtr context, IntPtr reserved, out uint previous);
    [DllImport("wlanapi.dll")] static extern void WlanFreeMemory(IntPtr memory);
    [DllImport("wlanapi.dll")] static extern uint WlanScan(IntPtr handle, ref Guid id, IntPtr ssid, IntPtr ies, IntPtr reserved);
    public static uint RequestScan(string interfaceId) {
        Guid id=Guid.Parse(interfaceId);uint version;IntPtr handle;
        uint error=WlanOpenHandle(2,IntPtr.Zero,out version,out handle);
        if(error!=0)return error;
        try{return WlanScan(handle,ref id,IntPtr.Zero,IntPtr.Zero,IntPtr.Zero);}
        finally{WlanCloseHandle(handle,IntPtr.Zero);}
    }
    static readonly uint[] Opcodes = {1, 2, 3, 6, 8, 12, 0x10000101};
    static readonly string[] Names = {"autoconf", "background_scan", "media_streaming", "interface_state", "channel", "operation_mode", "statistics_raw"};
    static Dictionary<string, object> Query(IntPtr handle, Guid id, uint opcode) {
        uint size, type; IntPtr data;
        uint error = WlanQueryInterface(handle, ref id, opcode, IntPtr.Zero, out size, out data, out type);
        var row = new Dictionary<string, object> {{"error", error}, {"bytes", size}};
        try {
            if (error == 0 && data != IntPtr.Zero) {
                if (size > 65536) throw new InvalidOperationException("Unexpected WLAN query size");
                byte[] bytes = new byte[size]; Marshal.Copy(data, bytes, 0, bytes.Length);
                row["raw_base64"] = Convert.ToBase64String(bytes);
                if (size == 4) row["value"] = BitConverter.ToUInt32(bytes, 0);
            }
        } finally {if (data != IntPtr.Zero) WlanFreeMemory(data);}
        return row;
    }
    static object Snapshot(IntPtr handle, Guid id) {
        var result = new Dictionary<string, object>();
        for (int i=0; i<Opcodes.Length; i++) result[Names[i]] = Query(handle,id,Opcodes[i]);
        return result;
    }
    public static object Run(string interfaceId, int seconds, string stopFile, bool disableAutoconf, bool disableBackgroundScan) {
        if (seconds < 0 || seconds > 600) throw new ArgumentException("Observation budget exceeded");
        Guid id = Guid.Parse(interfaceId); uint version; IntPtr handle;
        uint error = WlanOpenHandle(2, IntPtr.Zero, out version, out handle);
        if (error != 0) throw new System.ComponentModel.Win32Exception((int)error);
        var notices = new List<object>(); var changes = new List<object>(); var watch = Stopwatch.StartNew();
        object before = null, after = null; int? originalAutoconf = null; uint? restoreError = null;
        var originalControls=new List<int[]>();
        Callback callback = delegate(ref Notice n, IntPtr context) {
            if (n.Interface != id) return;
            lock(notices) if(notices.Count < 4096) notices.Add(new {qpc_ticks=Stopwatch.GetTimestamp(), elapsed_ms=watch.Elapsed.TotalMilliseconds, source=n.Source, code=n.Code, bytes=n.Size});
        };
        try {
            before = Snapshot(handle,id); uint previous;
            error = WlanRegisterNotification(handle, 8|16, false, callback, IntPtr.Zero, IntPtr.Zero, out previous);
            changes.Add(new {operation="register_acm_msm_notifications", error=error});
            if (disableAutoconf) {
                var original=Query(handle,id,1);
                if (!original.ContainsKey("value")) throw new InvalidOperationException("Cannot preserve autoconf state");
                originalAutoconf=Convert.ToInt32(original["value"]);
                int value=0; error=WlanSetInterface(handle,ref id,1,4,ref value,IntPtr.Zero);
                changes.Add(new {operation="disable_autoconf", error=error, readback=Query(handle,id,1)});
                if(error!=0) throw new System.ComponentModel.Win32Exception((int)error);
            }
            if(disableBackgroundScan) {
                foreach(uint opcode in new uint[]{3,2}) {
                    var original=Query(handle,id,opcode);
                    if(!original.ContainsKey("value"))throw new InvalidOperationException("Cannot preserve scan control");
                    originalControls.Add(new int[]{(int)opcode,Convert.ToInt32(original["value"])});
                    int value=opcode==3?1:0;
                    error=WlanSetInterface(handle,ref id,opcode,4,ref value,IntPtr.Zero);
                    changes.Add(new {operation="set_scan_control",opcode=opcode,error=error,readback=Query(handle,id,opcode)});
                    if(error!=0)throw new System.ComponentModel.Win32Exception((int)error);
                }
            }
            while(watch.Elapsed.TotalSeconds < seconds && (String.IsNullOrEmpty(stopFile) || !File.Exists(stopFile))) Thread.Sleep(100);
            after=Snapshot(handle,id);
        } finally {
            originalControls.Reverse();
            foreach(var control in originalControls){int value=control[1];uint opcode=(uint)control[0];uint result=WlanSetInterface(handle,ref id,opcode,4,ref value,IntPtr.Zero);changes.Add(new{operation="restore_scan_control",opcode=opcode,error=result,readback=Query(handle,id,opcode)});}
            if(originalAutoconf.HasValue) {int value=originalAutoconf.Value;restoreError=WlanSetInterface(handle,ref id,1,4,ref value,IntPtr.Zero);changes.Add(new {operation="restore_autoconf", error=restoreError, readback=Query(handle,id,1)});}
            uint ignored; WlanRegisterNotification(handle,0,false,null,IntPtr.Zero,IntPtr.Zero,out ignored);
            WlanCloseHandle(handle,IntPtr.Zero); GC.KeepAlive(callback);
        }
        return new {interface_id=id, negotiated_version=version, qpc_frequency=Stopwatch.Frequency, seconds=watch.Elapsed.TotalSeconds,
            before=before, after=after, operations=changes, notifications=notices, restore_error=restoreError,
            limitation="Native WLAN notifications do not expose every firmware off-channel scan or TX queue depth"};
    }
}
