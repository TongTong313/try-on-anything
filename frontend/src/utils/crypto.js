import CryptoJS from 'crypto-js'

/**
 * 生成动态密钥（基于浏览器环境信息）
 * 注意：这种方式主要用于混淆，不能提供真正的安全性
 * 真正的安全应该依赖后端验证和HTTPS传输
 * @returns {string} 动态生成的密钥
 */
function generateDynamicKey() {
  // 收集浏览器环境信息作为密钥种子
  const seeds = [
    navigator.userAgent,
    navigator.language,
    screen.width.toString(),
    screen.height.toString(),
    new Date().getTimezoneOffset().toString(),
    'try-on-anything-salt-2025'
  ]
  // 使用SHA256生成固定长度的密钥
  return CryptoJS.SHA256(seeds.join('|')).toString()
}

// 动态生成的密钥（每个浏览器环境唯一）
const SECRET_KEY = generateDynamicKey()

/**
 * 加密API Key
 * @param {string} apiKey - 原始API Key
 * @returns {string} 加密后的API Key
 */
export function encryptApiKey(apiKey) {
  if (!apiKey) return ''
  try {
    return CryptoJS.AES.encrypt(apiKey, SECRET_KEY).toString()
  } catch (error) {
    console.error('加密失败:', error)
    return ''
  }
}

/**
 * 解密API Key
 * @param {string} encryptedApiKey - 加密的API Key
 * @returns {string} 解密后的API Key
 */
export function decryptApiKey(encryptedApiKey) {
  if (!encryptedApiKey) return ''
  try {
    const bytes = CryptoJS.AES.decrypt(encryptedApiKey, SECRET_KEY)
    return bytes.toString(CryptoJS.enc.Utf8)
  } catch (error) {
    console.error('解密失败:', error)
    return ''
  }
}

/**
 * 保存API Key到localStorage（加密存储）
 * @param {string} key - 存储键名
 * @param {string} apiKey - API Key
 */
export function saveApiKey(key, apiKey) {
  if (!apiKey) {
    localStorage.removeItem(key)
    return
  }
  const encrypted = encryptApiKey(apiKey)
  localStorage.setItem(key, encrypted)
}

/**
 * 从localStorage获取API Key（自动解密）
 * @param {string} key - 存储键名
 * @returns {string} 解密后的API Key
 */
export function getApiKey(key) {
  const encrypted = localStorage.getItem(key)
  if (!encrypted) return ''
  return decryptApiKey(encrypted)
}

/**
 * 删除API Key
 * @param {string} key - 存储键名
 */
export function removeApiKey(key) {
  localStorage.removeItem(key)
}
