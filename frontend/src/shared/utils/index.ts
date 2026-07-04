/**
 * 通用工具函数
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

/** 格式化日期为 yyyy-MM-dd */
export function formatDate(date: Date | string | number | null | undefined): string {
  if (!date) return '—'
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * 智能格式化时间
 * - 今天：显示 HH:mm
 * - 今年：显示 M/D HH:mm
 * - 其他：显示 YYYY-MM-DD
 */
export function formatTime(time: Date | string | number | null | undefined): string {
  if (!time) return '—'
  const date = new Date(time)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  if (isToday) {
    return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }
  const isThisYear = date.getFullYear() === now.getFullYear()
  if (isThisYear) {
    return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }
  return formatDateTime(date)
}

/**
 * 格式化为相对时间（如"5分钟前"、"2小时前"）
 * @param isoStr ISO 时间字符串
 * @param now 当前时间（用于测试或避免频繁创建 Date）
 */
export function formatRelativeTime(isoStr: string, now?: Date): string {
  const d = new Date(isoStr)
  const nowTime = now ?? new Date()
  const diffMs = nowTime.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour} 小时前`
  const diffDay = Math.floor(diffHour / 24)
  if (diffDay < 7) return `${diffDay} 天前`
  if (diffDay < 30) return `${Math.floor(diffDay / 7)} 周前`
  return `${d.getMonth() + 1}/${d.getDate()}`
}

/** 检查是否为空值（null / undefined / 空字符串） */
export function isEmpty(val: unknown): boolean {
  return val === null || val === undefined || val === ''
}
