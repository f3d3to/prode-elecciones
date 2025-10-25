/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE: string
  readonly VITE_DEADLINE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Allow importing .vue files in TS
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
