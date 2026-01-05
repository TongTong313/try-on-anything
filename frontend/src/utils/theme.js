/**
 * 主题管理工具函数
 * 支持浅色、深色和自动跟随系统三种模式
 */

const THEME_KEY = 'theme-preference'
const THEME_LIGHT = 'light'
const THEME_DARK = 'dark'
const THEME_AUTO = 'auto'

/**
 * 获取系统主题偏好
 * @returns {'light' | 'dark'} 系统主题
 */
export function getSystemTheme() {
  // 检测系统是否偏好深色模式
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return THEME_DARK
  }
  return THEME_LIGHT
}

/**
 * 应用主题到 HTML 根元素
 * @param {'light' | 'dark'} theme - 要应用的主题
 */
export function applyTheme(theme) {
  const htmlElement = document.documentElement

  if (theme === THEME_DARK) {
    htmlElement.classList.add('dark')
  } else {
    htmlElement.classList.remove('dark')
  }
}

/**
 * 从 localStorage 获取保存的主题偏好
 * @returns {'light' | 'dark' | 'auto' | null} 保存的主题偏好
 */
export function getSavedTheme() {
  try {
    return localStorage.getItem(THEME_KEY)
  } catch (error) {
    console.warn('Failed to get saved theme:', error)
    return null
  }
}

/**
 * 保存主题偏好到 localStorage
 * @param {'light' | 'dark' | 'auto'} theme - 要保存的主题偏好
 */
export function saveTheme(theme) {
  try {
    localStorage.setItem(THEME_KEY, theme)
  } catch (error) {
    console.warn('Failed to save theme:', error)
  }
}

/**
 * 初始化主题
 * 优先使用用户保存的偏好，否则跟随系统
 * @returns {'light' | 'dark' | 'auto'} 当前主题偏好
 */
export function initTheme() {
  const savedTheme = getSavedTheme()

  // 如果有保存的偏好，使用保存的偏好
  if (savedTheme) {
    if (savedTheme === THEME_AUTO) {
      // 自动模式：跟随系统
      const systemTheme = getSystemTheme()
      applyTheme(systemTheme)
    } else {
      // 手动模式：使用保存的主题
      applyTheme(savedTheme)
    }
    return savedTheme
  }

  // 没有保存的偏好，默认跟随系统
  const systemTheme = getSystemTheme()
  applyTheme(systemTheme)
  return THEME_AUTO
}

/**
 * 监听系统主题变化
 * @param {Function} callback - 系统主题变化时的回调函数
 * @returns {Function} 取消监听的函数
 */
export function watchSystemTheme(callback) {
  if (!window.matchMedia) {
    return () => {}
  }

  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

  const handler = (e) => {
    const theme = e.matches ? THEME_DARK : THEME_LIGHT
    callback(theme)
  }

  // 添加监听器
  mediaQuery.addEventListener('change', handler)

  // 返回取消监听的函数
  return () => {
    mediaQuery.removeEventListener('change', handler)
  }
}

// 导出常量
export { THEME_LIGHT, THEME_DARK, THEME_AUTO }
