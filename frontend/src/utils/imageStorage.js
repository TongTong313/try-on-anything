/**
 * 图片持久化存储工具
 * 使用 IndexedDB 存储任务相关的图片数据，解决页面切换后图片丢失的问题
 */

const DB_NAME = 'TryOnImageDB'
const DB_VERSION = 1
const STORE_NAME = 'taskImages'

let dbInstance = null

/**
 * 获取数据库实例
 */
function getDB() {
  return new Promise((resolve, reject) => {
    if (dbInstance) {
      resolve(dbInstance)
      return
    }

    const request = indexedDB.open(DB_NAME, DB_VERSION)

    request.onerror = () => {
      console.error('IndexedDB 打开失败:', request.error)
      reject(request.error)
    }

    request.onsuccess = () => {
      dbInstance = request.result
      resolve(dbInstance)
    }

    request.onupgradeneeded = (event) => {
      const db = event.target.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'taskId' })
      }
    }
  })
}

/**
 * 将 File 对象转换为 Base64 字符串
 */
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    if (!file) {
      resolve(null)
      return
    }
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

/**
 * 将 Base64 字符串转换为 File 对象
 */
function base64ToFile(base64, fileName, mimeType) {
  if (!base64) return null

  try {
    const arr = base64.split(',')
    const mime = mimeType || arr[0].match(/:(.*?);/)?.[1] || 'image/png'
    const bstr = atob(arr[1])
    let n = bstr.length
    const u8arr = new Uint8Array(n)
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n)
    }
    return new File([u8arr], fileName || 'image.png', { type: mime })
  } catch (error) {
    console.error('Base64 转 File 失败:', error)
    return null
  }
}

/**
 * 保存任务的图片数据到 IndexedDB
 * @param {string} taskId - 任务ID
 * @param {Object} images - 包含图片 File 对象的对象
 */
export async function saveTaskImages(taskId, images) {
  if (!taskId || !images) return

  try {
    const db = await getDB()

    // 将 File 对象转换为 Base64
    const imageData = {
      taskId,
      jewelryImage: await fileToBase64(images.jewelryImage),
      clothingImage: await fileToBase64(images.clothingImage),
      personImage: await fileToBase64(images.personImage),
      savedAt: Date.now()
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], 'readwrite')
      const store = transaction.objectStore(STORE_NAME)
      const request = store.put(imageData)

      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  } catch (error) {
    console.error('保存图片到 IndexedDB 失败:', error)
  }
}

/**
 * 从 IndexedDB 加载任务的图片数据
 * @param {string} taskId - 任务ID
 * @returns {Object|null} 包含 File 对象的对象
 */
export async function loadTaskImages(taskId) {
  if (!taskId) return null

  try {
    const db = await getDB()

    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], 'readonly')
      const store = transaction.objectStore(STORE_NAME)
      const request = store.get(taskId)

      request.onsuccess = () => {
        const data = request.result
        if (!data) {
          resolve(null)
          return
        }

        // 将 Base64 转换回 File 对象
        resolve({
          jewelryImage: base64ToFile(data.jewelryImage, 'jewelry.png'),
          clothingImage: base64ToFile(data.clothingImage, 'clothing.png'),
          personImage: base64ToFile(data.personImage, 'person.png')
        })
      }
      request.onerror = () => reject(request.error)
    })
  } catch (error) {
    console.error('从 IndexedDB 加载图片失败:', error)
    return null
  }
}

/**
 * 删除任务的图片数据
 * @param {string} taskId - 任务ID
 */
export async function deleteTaskImages(taskId) {
  if (!taskId) return

  try {
    const db = await getDB()

    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], 'readwrite')
      const store = transaction.objectStore(STORE_NAME)
      const request = store.delete(taskId)

      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  } catch (error) {
    console.error('删除 IndexedDB 图片数据失败:', error)
  }
}

/**
 * 清理所有不在任务列表中的图片数据（防止数据泄漏）
 * @param {Array<string>} validTaskIds - 有效的任务ID列表
 */
export async function cleanupOrphanImages(validTaskIds) {
  try {
    const db = await getDB()
    const validSet = new Set(validTaskIds)

    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], 'readwrite')
      const store = transaction.objectStore(STORE_NAME)
      const request = store.openCursor()

      request.onsuccess = (event) => {
        const cursor = event.target.result
        if (cursor) {
          if (!validSet.has(cursor.key)) {
            cursor.delete()
          }
          cursor.continue()
        } else {
          resolve()
        }
      }
      request.onerror = () => reject(request.error)
    })
  } catch (error) {
    console.error('清理孤立图片数据失败:', error)
  }
}
