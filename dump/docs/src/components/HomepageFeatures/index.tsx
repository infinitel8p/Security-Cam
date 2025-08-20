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
    title: 'Night Vision:',
    Svg: require('@site/static/img/undraw_surveillance.svg').default,
    description: (
      <>
        Elevating the Raspberry Pi Zero 2 W along with the Waveshare RPi Camera (F) for a complete view - even in the dark.
      </>
    ),
  },
  {
    title: 'Device Detection:',
    Svg: require('@site/static/img/undraw_broadcast.svg').default,
    description: (
      <>
        Integration with WiFi Access Point and Bluetooth to prevent recording when you are nearby.
      </>
    ),
  },
  {
    title: 'Admin Dashboard:',
    Svg: require('@site/static/img/undraw_responsive.svg').default,
    description: (
      <>
        Check the status of your camera, view the live feed, download recordings, and change settings on all your devices.
      </>
    ),
  },
];

function Feature({ title, Svg, description }: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
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
