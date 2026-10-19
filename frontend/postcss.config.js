// postcss 配置：移动端 px → vw 自动转换
// 仅对 src/mobile/ 目录生效，不影响 web 端
import pxToViewport from 'postcss-px-to-viewport-8-plugin'

export default {
  plugins: [
    pxToViewport({
      viewportWidth: 375,
      unitPrecision: 5,
      viewportUnit: 'vw',
      selectorBlackList: [],
      minPixelValue: 1,
      mediaQuery: false,
      // 排除所有非移动端文件（桌面端保持 px 单位）
      exclude: [/\/node_modules\//, /\/src\/(?!mobile\/)/],
    }),
  ],
}
