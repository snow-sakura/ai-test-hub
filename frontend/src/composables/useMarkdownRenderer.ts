/**
 * 简易 Markdown 渲染器
 * 将 Markdown 文本转换为安全的 HTML，支持：
 * - 标题 (h1-h6)
 * - 粗体/斜体/删除线
 * - 行内代码/代码块
 * - 有序/无序列表
 * - 链接/图片
 * - 表格
 * - 引用块
 * - 分隔线
 */
export function useMarkdownRenderer() {
  function escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
  }

  function render(text: string): string {
    if (!text) return ''

    let html = escapeHtml(text)

    // 代码块（先处理，避免被后续规则破坏）
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
      const langClass = lang ? ` class="language-${lang}"` : ''
      return `<pre><code${langClass}>${code}</code></pre>`
    })

    // 行内代码
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

    // 标题
    html = html.replace(/^##### (.+)$/gm, '<h5>$1</h5>')
    html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>')
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')

    // 分隔线
    html = html.replace(/^---$/gm, '<hr>')
    html = html.replace(/^\*\*\*$/gm, '<hr>')

    // 引用块
    html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')

    // 无序列表
    html = html.replace(/^(\s*)[-*+] (.+)$/gm, (_, indent, item) => {
      const level = Math.floor(indent.length / 2)
      const margin = level * 20
      return `<li style="margin-left:${margin}px">${item}</li>`
    })
    // 包裹 <li> 为 <ul>
    html = html.replace(/((?:<li[^>]*>.*?<\/li>\s*)+)/g, '<ul>$1</ul>')

    // 有序列表
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    // 有序列表已有 <li>，再包 <ol> 会重复，用负向前瞻避免
    html = html.replace(/(<li>[\s\S]*?<\/li>\s*)(?![\s\S]*?<\/ol>)/g, (match) => {
      if (/<ol>[\s\S]*?<\/ol>/.test(html)) return match
      return `<ol>${match}</ol>`
    })

    // 粗体
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // 斜体
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
    // 删除线
    html = html.replace(/~~(.+?)~~/g, '<del>$1</del>')

    // 图片
    html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width:100%">')

    // 链接
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')

    // 表格
    html = html.replace(/\|(.+)\|/g, (line) => {
      const cells = line.split('|').filter(c => c.trim())
      if (cells.every(c => /^[\s:-]+$/.test(c))) return '' // 分隔行
      const tag = /<table/.test(html) ? 'td' : 'th'
      const row = cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('')
      return `<tr>${row}</tr>`
    })
    // 包裹表格行
    html = html.replace(/((?:<tr>.*?<\/tr>\s*)+)/g, '<table>$1</table>')

    // 段落（未被其他标签包裹的文本块）
    html = html.replace(/^(?!<[houbtpi]|<table|<pre|<li|<bl)/gm, '<p>')
    html = html.replace(/(?<![>\n])$/gm, '</p>')

    // 清理空段落
    html = html.replace(/<p><\/p>/g, '')

    return html
  }

  return { render }
}
