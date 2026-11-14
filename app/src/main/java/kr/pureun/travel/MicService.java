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
            if (Build.VERSION.SDK_INT >= 30) startForeground(7, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE);
            else startForeground(7, n);
            if (wake == null) {
                PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
                wake = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "travel:listening");
                wake.setReferenceCounted(false);
            }
            wake.acquire(4 * 60 * 60 * 1000L);
        } catch (Throwable t) {
            Log.w(MainActivity.TAG, "service", t);
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
