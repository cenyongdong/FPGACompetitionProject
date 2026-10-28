using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using Microsoft.Kinect;

internal static class Snapshot
{
    public static int Main(string[] args)
    {
        if(args.Length != 1 || File.Exists(args[0])) return 2;
        KinectSensor sensor = null;
        ColorFrameReader reader = null;
        try
        {
            sensor = KinectSensor.GetDefault();
            if(sensor == null) throw new Exception("No default Kinect sensor.");
            reader = sensor.ColorFrameSource.OpenReader(); sensor.Open();
            var timer = Stopwatch.StartNew();
            while(timer.Elapsed.TotalSeconds < 15)
            {
                using(var frame = reader.AcquireLatestFrame())
                {
                    if(frame != null)
                    {
                        int width=frame.FrameDescription.Width, height=frame.FrameDescription.Height;
                        var bytes=new byte[width*height*4];
                        frame.CopyConvertedFrameDataToArray(bytes,ColorImageFormat.Bgra);
                        using(var bitmap=new Bitmap(width,height,PixelFormat.Format32bppArgb))
                        {
                            var data=bitmap.LockBits(new Rectangle(0,0,width,height),ImageLockMode.WriteOnly,PixelFormat.Format32bppArgb);
                            try { Marshal.Copy(bytes,0,data.Scan0,bytes.Length); }
                            finally { bitmap.UnlockBits(data); }
                            bitmap.Save(args[0],ImageFormat.Png);
                        }
                        File.WriteAllText(args[0]+".json","{\"source\":\"actual Kinect v2 ColorFrame\",\"width\":"+width+",\"height\":"+height+",\"sensor_relative_ticks_100ns\":"+frame.RelativeTime.Ticks+",\"host_saved_utc\":\""+DateTimeOffset.UtcNow.ToString("o")+"\"}");
                        Console.WriteLine(Path.GetFullPath(args[0])); return 0;
                    }
                }
                Thread.Sleep(10);
            }
            throw new TimeoutException("No color frame within 15 seconds.");
        }
        catch(Exception e) { Console.Error.WriteLine(e); return 1; }
        finally { if(reader!=null)reader.Dispose();if(sensor!=null)sensor.Close();Console.WriteLine("color_reader_disposed; sensor_closed"); }
    }
}
