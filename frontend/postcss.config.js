// postcss 配置：移动端 px → vw 自动转换
// 仅对 src/mobile/ 目录生效，不影响 web 端
import pxToViewport from 'postcss-px-to-viewport-8-plugin'

export default {
  plugins: [
    pxToViewport({
      viewportWidth: 375,           // 设计稿基准宽度（iPhone 标准）
      unitPrecision: 5,             // vw 小数精度
      viewportUnit: 'vw',           // 转换单位
      selectorBlackList: [],        // 不过滤选择器
      minPixelValue: 1,             // 最小转换像素值
      mediaQuery: false,            // 不在媒体查询中转换
      // 仅转换 src/mobile/ 下的样式文件
      include: [/\/mobile\//],
      // 排除不需要转换的文件
      exclude: [/\/node_modules\//, /\/web\//, /\/shared\//],
    }),
  ],
}
