import Header from '@/components/layout/Header';
import Sidebar from '@/components/layout/Sidebar';
import styles from './dashboard-layout.module.css';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className={styles.wrapper}>
      <Header />
      <div className={styles.body}>
        <Sidebar />
        <main className={styles.content}>
          {children}
        </main>
      </div>
    </div>
  );
}
