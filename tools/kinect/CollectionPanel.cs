// Finite visual protocol controller. Uses saved real SDK joints for status only.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using System.Windows.Forms;

internal sealed class CollectionPanel : Form
{
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer();
    static string[][] Plans = {
        new [] {"自然站立，双臂略离身体", "双臂侧平举，保持T字形", "左臂侧平举，右臂放下", "右臂侧平举，左臂放下", "双肘弯曲，双手放在肩旁",
                "自然站立，双臂略离身体", "双臂侧平举，保持T字形", "左臂侧平举，右臂放下", "右臂侧平举，左臂放下", "双肘弯曲，双手放在肩旁"},
        new [] {"缓慢反复抬放双臂，最高到肩部", "左右交替缓慢抬臂，每次停留3秒", "双肘缓慢弯曲、伸直，双手不交叉", "双臂缓慢侧平举、放下，每次停留3秒", "自然站立，双臂略离身体",
                "缓慢反复抬放双臂，最高到肩部", "左右交替缓慢抬臂，每次停留3秒", "双肘缓慢弯曲、伸直，双手不交叉", "双臂缓慢侧平举、放下，每次停留3秒", "自然站立，双臂略离身体"},
        new [] {"中央位置：自然站立，双臂略张开", "中央位置：双臂侧平举", "中央位置：双肘弯曲，双手肩旁", "向左小半步，站稳后自然站立", "左侧位置：双臂侧平举",
                "左侧位置：双肘弯曲，双手肩旁", "回中央，再向右小半步，站稳后自然站立", "右侧位置：双臂侧平举", "右侧位置：双肘弯曲，双手肩旁", "回到中央，自然站立，双臂略张开"}
    };
    readonly string work, python, collector;
    string[] sessionTitles={"保持姿势","缓慢连续动作","左右位置变化"};
    readonly Label title = new Label(), action = new Label(), clock = new Label(), next = new Label(), status = new Label();
    readonly Button start = new Button(), stop = new Button();
    readonly ProgressBar progress = new ProgressBar();
    readonly System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer();
    Process worker;
    StreamWriter workerLog, events;
    string folder;
    int session = -1, phase = -1, mode = 0;
    long stageQpc, workerQpc;
    bool cancelled, sessionComplete;
    DateTime lastFrameUtc = DateTime.MinValue;
    readonly List<object> results = new List<object>();
    static double Since(long q) { return (Stopwatch.GetTimestamp()-q)/(double)Stopwatch.Frequency; }
    static string Quote(string value) { return "\"" + value.Replace("\"", "\\\"") + "\""; }
    static void Save(string path, object value) { File.WriteAllText(path, Json.Serialize(value)+"\n", new UTF8Encoding(false)); }
    void Event(string type, object data) { events.WriteLine(Json.Serialize(new {type=type, host_qpc=Stopwatch.GetTimestamp(), qpc_frequency_hz=Stopwatch.Frequency, data=data})); events.Flush(); }

    CollectionPanel(string root, string interpreter, string script)
    {
        work=root; python=interpreter; collector=script;
        string customPlan=Path.Combine(work,"protocol-plan.json");
        if(File.Exists(customPlan)){
            var parsed=Json.Deserialize<string[][]>(File.ReadAllText(customPlan,Encoding.UTF8));
            if(parsed.Length!=3)throw new ArgumentException("Three bounded sessions required");
            foreach(var instructions in parsed){if(instructions.Length!=10)throw new ArgumentException("Ten phases required");foreach(string instruction in instructions)if(String.IsNullOrWhiteSpace(instruction))throw new ArgumentException("Empty instruction");}
            Plans=parsed;
        }
        string customTitles=Path.Combine(work,"protocol-titles.json");
        if(File.Exists(customTitles)){sessionTitles=Json.Deserialize<string[]>(File.ReadAllText(customTitles,Encoding.UTF8));if(sessionTitles.Length!=3)throw new ArgumentException("Three session titles required");}
        Text="Kinect + 三路CSI：长时动作采集"; WindowState=FormWindowState.Maximized; MinimumSize=new Size(900,650);
        BackColor=Color.FromArgb(16,23,38); ForeColor=Color.White; Font=new Font("Microsoft YaHei UI",18);
        var layout=new TableLayoutPanel { Dock=DockStyle.Fill, Padding=new Padding(30), ColumnCount=1, RowCount=7 };
        foreach(float h in new float[]{12,35,15,13,10,5,10}) layout.RowStyles.Add(new RowStyle(SizeType.Percent,h));
        foreach(var label in new[]{title,action,clock,next,status}) {label.Dock=DockStyle.Fill;label.TextAlign=ContentAlignment.MiddleCenter;}
        title.Font=new Font(Font.FontFamily,27,FontStyle.Bold); action.Font=new Font(Font.FontFamily,39,FontStyle.Bold);
        clock.Font=new Font(Font.FontFamily,39,FontStyle.Bold); clock.ForeColor=Color.FromArgb(91,220,170);
        next.Font=new Font(Font.FontFamily,22); status.Font=new Font(Font.FontFamily,17);
        layout.Controls.Add(title,0,0);layout.Controls.Add(action,0,1);layout.Controls.Add(clock,0,2);layout.Controls.Add(next,0,3);layout.Controls.Add(status,0,4);
        progress.Dock=DockStyle.Fill;progress.Maximum=300;layout.Controls.Add(progress,0,5);
        var buttons=new FlowLayoutPanel {Dock=DockStyle.Fill,FlowDirection=FlowDirection.LeftToRight};
        start.Text="开始采集";start.AutoSize=true;start.Padding=new Padding(20,8,20,8);start.ForeColor=Color.Black;start.BackColor=Color.WhiteSmoke;start.UseVisualStyleBackColor=false;
        stop.Text="停止并保存";stop.AutoSize=true;stop.Padding=new Padding(20,8,20,8);stop.ForeColor=Color.Black;stop.BackColor=Color.WhiteSmoke;stop.UseVisualStyleBackColor=false;
        buttons.Controls.Add(start);buttons.Controls.Add(stop);layout.Controls.Add(buttons,0,6);Controls.Add(layout);
        title.Text="3段 × 5分钟，段间休息60秒";action.Text="准备好后点击“开始采集”";
        clock.Text="尚未打开相机";next.Text="正对Kinect，头脚完整入镜；不使用语音";
        status.Text="本窗口显示实际动作节奏；无开发板、模型推理或训练";
        start.Click+=delegate { if(mode==0){start.Enabled=false;BeginSession();} };
        stop.Click+=delegate { if(mode==6)Close();else RequestStop(); };
        FormClosing+=delegate(object sender,FormClosingEventArgs e) { if(worker!=null && !worker.HasExited){e.Cancel=true;RequestStop();} };
        timer.Interval=100;timer.Tick+=Tick;timer.Start();
        Shown+=delegate {using(var preview=new Bitmap(ClientSize.Width,ClientSize.Height)){DrawToBitmap(preview,new Rectangle(Point.Empty,ClientSize));preview.Save(Path.Combine(work,"panel-preview.png"));}};
        Save(Path.Combine(work,"panel-ready.json"),new {ready=true, pid=Process.GetCurrentProcess().Id, protocol=Plans, protocol_titles=sessionTitles});
    }
    void BeginSession()
    {
        session++;if(session>=Plans.Length){Finish(false);return;}
        folder=Path.Combine(work,"session-"+(session+1).ToString("D2"));
        if(Directory.Exists(folder))throw new IOException("Refusing to overwrite "+folder);
        phase=-1;sessionComplete=false;stageQpc=workerQpc=Stopwatch.GetTimestamp();mode=1;
        title.Text="第 "+(session+1)+" / 3 段："+sessionTitles[session];action.Text="自然站立，等待人体和三路CSI就绪";
        clock.Text="准备中，不计入5分钟";next.Text="第一组："+Plans[session][0];progress.Value=0;
        workerLog=new StreamWriter(Path.Combine(work,"session-"+(session+1).ToString("D2")+"-console.log"),false,new UTF8Encoding(false));
        var info=new ProcessStartInfo(python,"-B "+Quote(collector)+" --output "+Quote(folder)+" --seconds 300 --panel") {UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true};
        worker=new Process {StartInfo=info};
        DataReceivedEventHandler log=delegate(object s,DataReceivedEventArgs e){if(e.Data!=null)lock(workerLog){workerLog.WriteLine(e.Data);workerLog.Flush();}};
        worker.OutputDataReceived+=log;worker.ErrorDataReceived+=log;worker.Start();worker.BeginOutputReadLine();worker.BeginErrorReadLine();
    }
    Dictionary<string,object> LatestBody()
    {
        string path=Path.Combine(folder,"kinect/bodies.jsonl");if(!File.Exists(path))return null;
        try {
            using(var file=new FileStream(path,FileMode.Open,FileAccess.Read,FileShare.ReadWrite)){
                long offset=Math.Max(0,file.Length-40000);file.Seek(offset,SeekOrigin.Begin);
                using(var reader=new StreamReader(file,Encoding.UTF8)){
                    string text=reader.ReadToEnd();string[] lines=text.Split('\n');
                    for(int i=lines.Length-2;i>=0;i--){try{return Json.Deserialize<Dictionary<string,object>>(lines[i]);}catch{}}
                }
            }
        }catch{}return null;
    }
    void RequestStop()
    {
        cancelled=true;mode=5;action.Text="正在停止并保存，请稍候";next.Text="不会继续下一段";
        if(folder!=null && Directory.Exists(folder)){
            File.WriteAllText(Path.Combine(folder,"cancel.request"),"User requested stop");
            File.WriteAllText(Path.Combine(folder,"kinect-stop.request"),"User requested stop");
        }
        if(worker==null || worker.HasExited)Finish(true);
    }
    void Finish(bool stopped)
    {
        timer.Stop();mode=6;
        Save(Path.Combine(work,"panel-result.json"),new {user_stopped=stopped, sessions=results, completed_sessions=results.Count, board_used=false, training_started=false});
        title.Text=stopped?"采集已停止":"三段采集已完成";action.Text="数据已保存，可以休息";clock.Text="相机与接收程序均已退出";
        next.Text="代理将检查关节质量与CSI连续性";status.Text=work;
        stop.Text="关闭窗口";start.Visible=false;
        // Closing is automatic, so the elevated wrapper can restore the network.
        var closeTimer=new System.Windows.Forms.Timer {Interval=5000};closeTimer.Tick+=delegate{closeTimer.Stop();Close();};closeTimer.Start();
    }
    void Tick(object sender,EventArgs args)
    {
        try {
            if(mode==0 || mode==6)return;
            if(worker!=null && worker.HasExited && mode!=4){
                worker.WaitForExit();int exit=worker.ExitCode;workerLog.Dispose();workerLog=null;
                if(events!=null){events.Dispose();events=null;}
                results.Add(new {session=session+1,directory=folder,exit_code=exit,protocol_complete=sessionComplete});worker.Dispose();worker=null;
                if(cancelled || exit!=0 || !sessionComplete){Finish(true);return;}
                if(session==2){Finish(false);return;}
                mode=4;stageQpc=Stopwatch.GetTimestamp();title.Text="第 "+(session+1)+" 段已保存";action.Text="休息60秒";next.Text="下一段："+sessionTitles[session+1];
            }
            if(mode==5)return;
            if(mode==4){double remain=60-Since(stageQpc);clock.Text="休息剩余 "+Math.Max(0,(int)Math.Ceiling(remain))+" 秒";if(remain<=0)BeginSession();return;}
            var frame=LatestBody();bool one=frame!=null && Convert.ToInt32(frame["body_count"])==1;
            if(frame!=null){status.Text="当前人体数："+frame["body_count"]+"　　保持头脚入镜、正对镜头";lastFrameUtc=DateTime.UtcNow;}
            if(mode==1){
                if(Since(workerQpc)>80){RequestStop();return;}
                if(one){mode=2;stageQpc=Stopwatch.GetTimestamp();action.Text="准备开始："+Plans[session][0];}
                return;
            }
            if(mode==2){double remain=8-Since(stageQpc);clock.Text="正式开始倒计时 "+Math.Max(0,(int)Math.Ceiling(remain))+" 秒";
                if(remain>0)return;
                events=new StreamWriter(Path.Combine(folder,"visual-protocol.jsonl"),false,new UTF8Encoding(false));
                stageQpc=Stopwatch.GetTimestamp();mode=3;Event("start",new {session=session+1,duration_seconds=300,instructions=Plans[session]});
            }
            if(mode==3){
                double elapsed=Since(stageQpc);int index=Math.Min(9,(int)(elapsed/30));
                if(index!=phase){phase=index;action.Text=Plans[session][phase];title.Text="第 "+(session+1)+" / 3 段　动作 "+(phase+1)+" / 10";next.Text=phase<9?"下一组："+Plans[session][phase+1]:"本段完成后休息";Event("phase",new {phase=phase,instruction=Plans[session][phase]});}
                clock.Text="当前动作剩余 "+Math.Max(0,(int)Math.Ceiling(30-elapsed%30))+" 秒　／　本段剩余 "+Math.Max(0,(int)Math.Ceiling(300-elapsed))+" 秒";
                progress.Value=Math.Min(300,(int)elapsed);
                if(elapsed>=300){Event("end",new {completed=true});sessionComplete=true;mode=7;action.Text="本段完成，正在保存";File.WriteAllText(Path.Combine(folder,"kinect-stop.request"),"Visual protocol complete");}
            }
        }catch(Exception error){Save(Path.Combine(work,"panel-error.json"),new {error=error.ToString()});RequestStop();}
    }
    [STAThread]
    static void Main(string[] args)
    {
        if(args.Length!=3)throw new ArgumentException("WORK PYTHON COLLECTOR required");
        Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Application.Run(new CollectionPanel(Path.GetFullPath(args[0]),args[1],args[2]));
    }
}
