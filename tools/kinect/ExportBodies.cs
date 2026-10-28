// Kinect v2 diagnostic capture. Does not access CSI, networking, or models.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Threading;
using System.Web.Script.Serialization;
using Microsoft.Kinect;

internal static class ExportBodies
{
    private static volatile bool cancelled;
    private static readonly JavaScriptSerializer Json = new JavaScriptSerializer();
    private static Dictionary<string, object> Row(params object[] pairs)
    {
        var result = new Dictionary<string, object>();
        for (int i = 0; i < pairs.Length; i += 2) result[(string)pairs[i]] = pairs[i + 1];
        return result;
    }
    private static bool Finite(float x) { return !Single.IsNaN(x) && !Single.IsInfinity(x); }
    private static object Number(float x) { return Finite(x) ? (object)x : null; }
    private static void Save(string path, object value)
    {
        using (var file = new StreamWriter(new FileStream(path, FileMode.CreateNew), new System.Text.UTF8Encoding(false)))
            file.WriteLine(Json.Serialize(value));
    }
    public static int Main(string[] args)
    {
        bool depthDiagnostic = false;
        string stopFile = null;
        if (args.Length < 2)
        {
            Console.WriteLine("Usage: ExportBodies.exe NEW_OUTPUT_DIRECTORY SECONDS(1..600) [--depth-diagnostic] [--stop-file FILE]");
            return 2;
        }
        for (int i = 2; i < args.Length; ++i)
        {
            if (args[i] == "--depth-diagnostic") depthDiagnostic = true;
            else if (args[i] == "--stop-file" && i + 1 < args.Length) stopFile = Path.GetFullPath(args[++i]);
            else return 2;
        }
        double seconds;
        if (!Double.TryParse(args[1], NumberStyles.Float, CultureInfo.InvariantCulture, out seconds) ||
            Double.IsNaN(seconds) || Double.IsInfinity(seconds) || seconds < 1 || seconds > 600)
            return 2;
        string directory = Path.GetFullPath(args[0]);
        if (Directory.Exists(directory) || File.Exists(directory))
        {
            Console.Error.WriteLine("Refusing to overwrite an existing capture directory.");
            return 2;
        }
        Directory.CreateDirectory(directory);
        Console.CancelKeyPress += delegate(object sender, ConsoleCancelEventArgs e) { cancelled = true; e.Cancel = true; };
        KinectSensor sensor = null;
        BodyFrameReader reader = null;
        DepthFrameReader depthReader = null;
        bool depthSaved = false;
        string error = null;
        long frames = 0, bodyFrames = 0, bodiesTotal = 0, duplicates = 0, backwards = 0, nonfinite = 0;
        long? firstTimestamp = null, lastTimestamp = null;
        var identities = new HashSet<string>();
        bool sensorClosed = false, readerDisposed = false;
        bool requestedStop = false;
        var started = DateTimeOffset.UtcNow;
        var runtime = Stopwatch.StartNew();
        try
        {
            sensor = KinectSensor.GetDefault();
            if (sensor == null) throw new InvalidOperationException("SDK GetDefault returned no sensor.");
            Save(Path.Combine(directory, "metadata.json"), Row(
                "schema", "KINECT2-BODIES1", "sdk_assembly", typeof(KinectSensor).Assembly.FullName,
                "sdk_assembly_path", typeof(KinectSensor).Assembly.Location,
                "started_utc", started.ToString("o"), "requested_capture_seconds", seconds,
                "initial_is_available", sensor.IsAvailable,
                "joint_names", Enum.GetNames(typeof(JointType)), "position_units", "metres",
                "coordinate_system", "SDK camera space; unchanged; no mapping to WiFi model labels",
                "sensor_time", "BodyFrame.RelativeTime.Ticks; each tick is 100 ns; device-relative, not UTC",
                "host_time", "host timestamps bracket AcquireLatestFrame; not sensor exposure time or cross-device synchronization",
                "host_qpc_frequency_hz", Stopwatch.Frequency,
                "camera_images_saved", depthDiagnostic,
                "requested_image_stream", depthDiagnostic ? "one raw depth diagnostic frame, no RGB" : "none",
                "CSI_capture", false, "model_training", false));
            reader = sensor.BodyFrameSource.OpenReader();
            if (depthDiagnostic) depthReader = sensor.DepthFrameSource.OpenReader();
            var bodies = new Body[sensor.BodyFrameSource.BodyCount];
            sensor.Open();
            var initialization = Stopwatch.StartNew();
            Stopwatch capture = null;
            double lastReport = -2;
            using (var stream = new StreamWriter(new FileStream(Path.Combine(directory, "bodies.jsonl"), FileMode.CreateNew), new System.Text.UTF8Encoding(false)))
            {
                while (!cancelled)
                {
                    if (stopFile != null && File.Exists(stopFile)) { requestedStop = true; break; }
                    if (capture == null && initialization.Elapsed.TotalSeconds >= 30)
                        throw new TimeoutException("No body frame within 30 seconds; IsAvailable=" + sensor.IsAvailable);
                    if (capture != null && capture.Elapsed.TotalSeconds >= seconds) break;
                    long qpcBefore = Stopwatch.GetTimestamp();
                    using (BodyFrame frame = reader.AcquireLatestFrame())
                    {
                        long qpcAfter = Stopwatch.GetTimestamp();
                        string hostUtc = DateTimeOffset.UtcNow.ToString("o");
                        if (frame != null)
                        {
                            if (capture == null) capture = Stopwatch.StartNew();
                            long timestamp = frame.RelativeTime.Ticks;
                            // Keep raw timestamp anomalies; do not repair or manufacture frames.
                            if (lastTimestamp.HasValue && timestamp == lastTimestamp.Value) ++duplicates;
                            if (lastTimestamp.HasValue && timestamp < lastTimestamp.Value) ++backwards;
                            if (!firstTimestamp.HasValue) firstTimestamp = timestamp;
                            lastTimestamp = timestamp;
                            frame.GetAndRefreshBodyData(bodies);
                            var people = new List<object>();
                            foreach (Body body in bodies)
                            {
                                if (body == null || !body.IsTracked) continue;
                                string identity = body.TrackingId.ToString(CultureInfo.InvariantCulture);
                                identities.Add(identity);
                                var joints = new List<object>();
                                foreach (JointType type in Enum.GetValues(typeof(JointType)))
                                {
                                    Joint joint = body.Joints[type];
                                    bool finite = Finite(joint.Position.X) && Finite(joint.Position.Y) && Finite(joint.Position.Z);
                                    if (!finite) ++nonfinite;
                                    joints.Add(Row("index", (int)type, "name", type.ToString(),
                                        "x", Number(joint.Position.X), "y", Number(joint.Position.Y), "z", Number(joint.Position.Z),
                                        "tracking_state", joint.TrackingState.ToString(), "finite", finite));
                                }
                                people.Add(Row("tracking_id", identity, "clipped_edges", body.ClippedEdges.ToString(), "joints", joints));
                            }
                            Vector4 floor = frame.FloorClipPlane;
                            stream.WriteLine(Json.Serialize(Row("schema", "KINECT2-BODIES1", "frame", ++frames,
                                "sensor_relative_ticks_100ns", timestamp,
                                "host_acquire_begin_qpc", qpcBefore, "host_acquire_end_qpc", qpcAfter,
                                "host_acquire_end_utc", hostUtc, "body_count", people.Count,
                                "floor_clip_plane", new object[] { Number(floor.X), Number(floor.Y), Number(floor.Z), Number(floor.W) },
                                "bodies", people)));
                            if (people.Count > 0) ++bodyFrames;
                            bodiesTotal += people.Count;
                            if (frames % 30 == 0) stream.Flush();
                        }
                    }
                    if (depthReader != null && !depthSaved && capture != null && capture.Elapsed.TotalSeconds > 1)
                    {
                        using (DepthFrame depth = depthReader.AcquireLatestFrame())
                        {
                            if (depth != null)
                            {
                                int width = depth.FrameDescription.Width, height = depth.FrameDescription.Height;
                                var pixels = new ushort[width * height];
                                depth.CopyFrameDataToArray(pixels);
                                var bytes = new byte[pixels.Length * 2];
                                Buffer.BlockCopy(pixels, 0, bytes, 0, bytes.Length);
                                File.WriteAllBytes(Path.Combine(directory, "depth.u16le"), bytes);
                                Save(Path.Combine(directory, "depth.json"), Row("width", width, "height", height,
                                    "units", "millimetres", "dtype", "uint16 little-endian",
                                    "sensor_relative_ticks_100ns", depth.RelativeTime.Ticks,
                                    "min_reliable_mm", depth.DepthMinReliableDistance,
                                    "max_reliable_mm", depth.DepthMaxReliableDistance));
                                depthSaved = true;
                            }
                        }
                    }
                    if (runtime.Elapsed.TotalSeconds - lastReport >= 2)
                    {
                        lastReport = runtime.Elapsed.TotalSeconds;
                        Console.WriteLine("elapsed={0:F1}s available={1} frames={2} frames_with_bodies={3}",
                            runtime.Elapsed.TotalSeconds, sensor.IsAvailable, frames, bodyFrames);
                    }
                    Thread.Sleep(5);
                }
            }
        }
        catch (Exception e) { error = e.ToString(); Console.Error.WriteLine(error); }
        finally
        {
            try { if (reader != null) reader.Dispose(); readerDisposed = true; }
            catch (Exception e) { error = (error ?? "") + "\nReader disposal: " + e; }
            try { if (depthReader != null) depthReader.Dispose(); }
            catch (Exception e) { error = (error ?? "") + "\nDepth reader disposal: " + e; }
            try { if (sensor != null) sensor.Close(); sensorClosed = true; }
            catch (Exception e) { error = (error ?? "") + "\nSensor close: " + e; }
            var outcome = Row("schema", "KINECT2-CAPTURE-RESULT1", "completed_utc", DateTimeOffset.UtcNow.ToString("o"),
                "elapsed_seconds", runtime.Elapsed.TotalSeconds, "frames", frames, "frames_with_bodies", bodyFrames,
                "total_body_observations", bodiesTotal, "distinct_tracking_ids", identities.Count,
                "first_sensor_ticks_100ns", firstTimestamp, "last_sensor_ticks_100ns", lastTimestamp,
                "duplicate_timestamps", duplicates, "backwards_timestamps", backwards, "nonfinite_joint_observations", nonfinite,
                "cancelled", cancelled, "requested_stop", requestedStop, "reader_disposed", readerDisposed, "sensor_closed", sensorClosed,
                "skeleton_export_observed", bodyFrames > 0, "depth_diagnostic_saved", depthSaved, "error", error);
            Save(Path.Combine(directory, "result.json"), outcome);
            Console.WriteLine(Json.Serialize(outcome));
        }
        return error != null ? 1 : bodyFrames == 0 ? 3 : 0;
    }
}
