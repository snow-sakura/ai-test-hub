/**
 * 通用工具函数
 * 预留：后续按需补充常用工具函数
 */

/** 格式化日期为 yyyy-MM-dd HH:mm:ss */
export function formatDateTime(date: Date | string | number): string {
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  const sec = String(d.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${min}:${sec}`
}

/** 检查是否为空值（null / undefined / 空字符串） */
export function isEmpty(val: unknown): boolean {
  return val === null || val === undefined || val === ''
}
