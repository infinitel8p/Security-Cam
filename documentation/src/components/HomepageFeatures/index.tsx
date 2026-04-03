import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  Svg: React.ComponentType<React.ComponentProps<'svg'>>;
  description: JSX.Element;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Night Vision',
    Svg: require('@site/static/img/undraw_surveillance.svg').default,
    description: (
      <>
        See clearly in complete darkness with the Waveshare RPi Camera (F) and its built-in infrared LEDs.
      </>
    ),
  },
  {
    title: 'Smart Presence Detection',
    Svg: require('@site/static/img/undraw_broadcast.svg').default,
    description: (
      <>
        Automatically suppress recording when your phone is nearby via Bluetooth or WiFi - no false alarms when you're home.
      </>
    ),
  },
  {
    title: 'Dashboard',
    Svg: require('@site/static/img/undraw_responsive.svg').default,
    description: (
      <>
        Live feed, video archive, system health, and settings - all from any device on your network.
      </>
    ),
  },
];

function Feature({ title, Svg, description }: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className={styles.featureCard}>
        <div className="text--center">
          <Svg className={styles.featureSvg} role="img" />
        </div>
        <div className="text--center padding-horiz--md">
          <Heading as="h3">{title}</Heading>
          <p>{description}</p>
        </div>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): JSX.Element {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
