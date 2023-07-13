import React from 'react'
import { useRouter } from 'next/router'
import { DocsThemeConfig } from 'nextra-theme-docs'

const config: DocsThemeConfig = {
  project: {
    link: 'https://github.com/bentoml/openllm',
  },
  chat: {
    link: 'https://l.bentoml.com/join-openllm-discord',
  },
  docsRepositoryBase: 'https://github.com/bentoml/openllm',
  footer: { text: 'BentoML' },
  useNextSeoProps() {
    const { asPath } = useRouter()
    if (asPath !== '/') {
      return {
        titleTemplate: '%s – OpenLLM',
      }
    }
  },
  i18n: [
    { locale: 'en-US', text: 'English' },
    { locale: 'zh-TW', text: '繁體中文' },
    { locale: 'zh-CN', text: '简体中文' },
  ],
  logo: (
    <>
      <img
        src='/logo-dark.svg'
        style={{ height: 20, objectFit: 'contain' }}
        alt='bentoml'
      />
      <img
        src='/logo-light.svg'
        style={{ height: 20, objectFit: 'contain' }}
        alt='bentoml'
      />
      <span style={{ marginLeft: '.4em', fontWeight: 800 }}>OpenLLM</span>
    </>
  ),
  logoLink: 'https://github.com/bentoml/openllm',
}

export default config
