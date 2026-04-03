import {type ReactNode} from 'react';
import Link from '@docusaurus/Link';
import styles from '../styles.module.css';

export default function NotFoundContent(): ReactNode {
  return (
    <div className={styles.container}>
      <div className={styles.camera}>
        <div className={styles.cameraBody}>
          <div className={styles.lens}>
            <div className={styles.lensInner}>
              <div className={styles.lensCore} />
            </div>
          </div>
        </div>
        <div className={styles.cameraMount} />
      </div>
      <h1 className={styles.title}>404</h1>
      <p className={styles.subtitle}>
        Nothing to see here - this area is not under surveillance.
      </p>
      <Link className="button button--primary button--lg" to="/">
        Back to safety
      </Link>
    </div>
  );
}
