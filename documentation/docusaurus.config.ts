import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Security-Cam',
  tagline: 'A DIY security camera for the Raspberry Pi Zero 2 W - records when it matters, stays quiet when you\'re home.',
  favicon: 'img/favicon.png',

  url: process.env.DOCS_URL || 'https://dev.infinitel8p.com',
  baseUrl: process.env.DOCS_BASE_URL || '/Security-Cam/',
  trailingSlash: false,
  organizationName: 'infinitel8p',
  projectName: 'Security-Cam',

  onBrokenLinks: process.env.DOCS_BASE_URL ? 'warn' : 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  plugins: ['@docusaurus/theme-live-codeblock', 'docusaurus-plugin-image-zoom'],

  presets: [
    [
      'classic',
      {
        docs: {
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.ts'),
          editUrl: 'https://github.com/infinitel8p/Security-Cam/edit/main/documentation/',
          showLastUpdateTime: true,
          showLastUpdateAuthor: true,
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    zoom: {
      selector: '.markdown img',
      background: {
        light: 'rgba(255, 255, 255, 0.9)',
        dark: 'rgba(18, 16, 25, 0.9)',
      },
    },
    liveCodeBlock: {
      /**
       * The position of the live playground, above or under the editor
       * Possible values: "top" | "bottom"
       */
      playgroundPosition: 'bottom',
    },
    // Replace with your project's social card
    image: 'img/social-card.webp',
    navbar: {
      title: 'Security-Cam',
      logo: {
        alt: 'Security-Cam Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'Documentation',
        },
        ...(process.env.DOCS_BASE_URL ? [{
          href: '/',
          label: 'Dashboard',
          position: 'left' as const,
        }] : []),
        {
          href: 'https://github.com/infinitel8p/Security-Cam',
          label: 'GitHub',
          position: 'right',
        },
        {
          href: 'https://github.com/infinitel8p/Security-Cam/releases',
          label: 'Releases',
          position: 'right',
        },
      ],
    },
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: true,
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Intro',
              to: '/intro',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'Ludo - GitHub',
              href: 'https://github.com/infinitel8p',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/infinitel8p/Security-Cam',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} InfiniteL8p`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
    algolia: {
      appId: 'HBU6GZICYZ',
      apiKey: '06fb9e308006070519f922b70996e210',
      indexName: 'infinitel8p',
      contextualSearch: true,

      // Optional: Specify domains where the navigation should occur through window.location instead on history.push. Useful when our Algolia config crawls multiple documentation sites and we want to navigate with window.location.href to them.
      // externalUrlRegex: 'external\\.com|domain\\.com',

      // Optional: Replace parts of the item URLs from Algolia. Useful when using the same search index for multiple deployments using a different baseUrl. You can use regexp or string in the `from` param. For example: localhost:3000 vs myCompany.com/docs
      replaceSearchResultPathname: {
        from: '/', // or as RegExp: /\/docs\//
        to: '/',
      },

      // Optional: Algolia search parameters
      searchParameters: {},

      // Optional: path for search page that enabled by default (`false` to disable it)
      searchPagePath: 'search',

      // Optional: whether the insights feature is enabled or not on Docsearch (`false` by default)
      insights: false,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
