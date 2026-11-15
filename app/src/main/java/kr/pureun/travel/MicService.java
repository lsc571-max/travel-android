package kr.pureun.travel;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.IBinder;
import android.os.PowerManager;
import android.util.Log;

/** 마이크로 듣는 동안 켜 두는 서비스: 화면을 꺼도 앱이 계속 듣고 통역할 수 있게 한다. */
public class MicService extends Service {
    private static final String CH = "listening";
    private PowerManager.WakeLock wake;

    /** 폰 소리 녹음 허락을 받은 뒤 결과를 돌려받을 곳 (p = null이면 실패. refused = 사용자가 허락하지 않음) */
    interface CapCb { void done(android.media.projection.MediaProjection p, boolean refused); }
    private static CapCb capCb;

    /** 폰에서 나오는 소리를 녹음하는 방식으로 시작: 서비스가 뜬 뒤에야 녹음 권한(MediaProjection)을 받을 수 있음 */
    static void startCapture(Context c, int code, Intent data, CapCb cb) {
        try {
            capCb = cb;
            Intent i = new Intent(c, MicService.class).putExtra("cap", true).putExtra("code", code).putExtra("data", data);
            if (Build.VERSION.SDK_INT >= 26) c.startForegroundService(i); else c.startService(i);
        } catch (Throwable t) { Log.w(MainActivity.TAG, "capture start", t); capCb = null; cb.done(null, false); }
    }

    static void start(Context c) {
        try {
            Intent i = new Intent(c, MicService.class);
            if (Build.VERSION.SDK_INT >= 26) c.startForegroundService(i); else c.startService(i);
        } catch (Throwable t) { Log.w(MainActivity.TAG, "service start", t); }
    }

    static void stop(Context c) {
        try { c.stopService(new Intent(c, MicService.class)); } catch (Throwable ignored) { }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        try {
            NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            if (Build.VERSION.SDK_INT >= 26 && nm.getNotificationChannel(CH) == null) {
                NotificationChannel ch = new NotificationChannel(CH, "듣는 중", NotificationManager.IMPORTANCE_LOW);
                ch.setShowBadge(false);
                nm.createNotificationChannel(ch);
            }
            Intent open = new Intent(this, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
            PendingIntent pi = PendingIntent.getActivity(this, 0, open, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
            Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(this, CH) : new Notification.Builder(this);
            Notification n = b.setContentTitle("여행 통역").setContentText("듣는 중입니다 · 화면을 꺼도 계속 통역합니다")
                    .setSmallIcon(android.R.drawable.ic_btn_speak_now).setContentIntent(pi).setOngoing(true).build();
            final boolean cap = intent != null && intent.getBooleanExtra("cap", false);
            if (Build.VERSION.SDK_INT >= 30 && cap) {
                try { startForeground(7, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE | ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION); }
                catch (Throwable t) { Log.w(MainActivity.TAG, "fgs both", t); startForeground(7, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION); }   // 두 가지를 함께 못 걸면 폰 소리 녹음용으로만
            }
            else if (Build.VERSION.SDK_INT >= 29 && cap) startForeground(7, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION);
            else if (Build.VERSION.SDK_INT >= 30) startForeground(7, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE);
            else startForeground(7, n);
            if (cap) {                                          // 서비스가 뜬 다음에 폰 소리 녹음 권한을 받음
                CapCb cb = capCb; capCb = null;
                android.media.projection.MediaProjection p = null;
                try {
                    android.media.projection.MediaProjectionManager mpm = (android.media.projection.MediaProjectionManager) getSystemService(MEDIA_PROJECTION_SERVICE);
                    Intent data = intent.getParcelableExtra("data");
                    p = mpm.getMediaProjection(intent.getIntExtra("code", 0), data);
                } catch (Throwable t) { Log.w(MainActivity.TAG, "projection", t); }
                if (cb != null) cb.done(p, false);
            }
            if (wake == null) {
                PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
                wake = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "travel:listening");
                wake.setReferenceCounted(false);
            }
            wake.acquire(4 * 60 * 60 * 1000L);
        } catch (Throwable t) {
            Log.w(MainActivity.TAG, "service", t);
            CapCb cb = capCb; capCb = null;
            if (cb != null) cb.done(null, false);
        }
        return START_NOT_STICKY;
    }

    @Override
    public void onDestroy() {
        try { if (wake != null && wake.isHeld()) wake.release(); } catch (Throwable ignored) { }
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
