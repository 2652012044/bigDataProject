<template>
  <div class="keyword-trend-page">
    <div class="page-header">
      <h2 class="page-title">关键词洞察</h2>
      <p class="page-desc">小说领域热门标签的热度、阅读量与关联关系可视化</p>
    </div>

    <el-row :gutter="20">
      <!-- 气泡图：关联书籍数 vs 平均阅读量 -->
      <el-col :span="16">
        <div class="card-box">
          <div class="card-header">
            <span class="card-title">关键词热度气泡图</span>
            <el-tooltip content="X轴=关联书籍数，Y轴=平均阅读量(万)，气泡大小=热度权重" placement="top">
              <el-icon class="help-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
          <div ref="bubbleChartRef" class="chart-container"></div>
        </div>
      </el-col>

      <!-- 右侧排行 -->
      <el-col :span="8">
        <div class="card-box rank-card">
          <div class="card-header">
            <span class="card-title">热度排行 TOP 15</span>
          </div>
          <div class="rank-list">
            <div v-for="(item, index) in topKeywords.slice(0, 15)" :key="item.keyword" class="rank-item" @click="highlightKeyword(item.keyword)">
              <div class="rank-num" :class="'rank-' + (index + 1)">{{ index + 1 }}</div>
              <div class="rank-info">
                <span class="rank-name">{{ item.keyword }}</span>
                <div class="rank-bar-bg">
                  <div class="rank-bar-fill" :style="{ width: item.barPercent + '%', background: barColors[index % barColors.length] }"></div>
                </div>
              </div>
              <span class="rank-count">{{ item.count }}本</span>
            </div>
          </div>
        </div>

        <div class="card-box insight-card">
          <div class="card-header"><span class="card-title">数据洞察</span></div>
          <div class="insight-list">
            <div class="insight-item" v-for="insight in insights" :key="insight.label">
              <span class="insight-dot" :style="{ background: insight.color }"></span>
              <span class="insight-text"><b>{{ insight.label }}</b>：{{ insight.value }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- 词云 -->
      <el-col :span="12">
        <div class="card-box">
          <div class="card-header"><span class="card-title">关键词词云</span></div>
          <div ref="wordcloudRef" class="chart-container-sm"></div>
        </div>
      </el-col>

      <!-- 漏斗图：高阅读量关键词 -->
      <el-col :span="12">
        <div class="card-box">
          <div class="card-header"><span class="card-title">高阅读量关键词漏斗</span></div>
          <div ref="funnelRef" class="chart-container-sm"></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import { QuestionFilled } from '@element-plus/icons-vue'
import request from '@/api/index'

const bubbleChartRef = ref(null)
const wordcloudRef = ref(null)
const funnelRef = ref(null)
let bubbleChart = null, wordcloudChart = null, funnelChart = null

const topKeywords = ref([])
const emergingKeywords = ref([])

const barColors = [
  '#667eea', '#764ba2', '#f093fb', '#43e97b', '#4facfe',
  '#fa709a', '#fccb90', '#a18cd1', '#38f9d7', '#fee140',
  '#5470c6', '#91cc75', '#ee6666', '#73c0de', '#fc8452'
]

const insights = computed(() => {
  if (topKeywords.value.length === 0) return []
  const top = topKeywords.value[0]
  const emerging = emergingKeywords.value.length > 0 ? emergingKeywords.value[0] : null
  const totalBooks = topKeywords.value.reduce((s, k) => s + k.count, 0)
  const avgCount = Math.round(totalBooks / topKeywords.value.length)
  return [
    { label: '最热门标签', value: `${top.keyword}（关联 ${top.count} 本）`, color: '#667eea' },
    { label: '最高阅读量', value: emerging ? `${emerging.keyword}（均阅 ${Number(emerging.avgReads).toLocaleString()}）` : '-', color: '#f093fb' },
    { label: '标签总数', value: `${topKeywords.value.length} 个`, color: '#43e97b' },
    { label: '平均关联', value: `${avgCount} 本/标签`, color: '#4facfe' },
  ]
})

async function loadData() {
  try {
    const res = await request.get('/trend/keyword')
    const data = res.data || {}
    const top = data.topKeywords || []
    emergingKeywords.value = data.emergingKeywords || []

    const maxCount = Math.max(...top.map(k => k.count), 1)
    topKeywords.value = top.map(k => ({ ...k, barPercent: Math.round(k.count * 100 / maxCount) }))

    initBubbleChart()
    initWordcloud()
    initFunnel()
  } catch (e) { /* keep empty */ }
}

function initBubbleChart() {
  if (!bubbleChartRef.value || emergingKeywords.value.length === 0) return
  if (bubbleChart) bubbleChart.dispose()
  bubbleChart = echarts.init(bubbleChartRef.value)

  const items = emergingKeywords.value
  const maxCount = Math.max(...items.map(k => k.count), 1)

  bubbleChart.setOption({
    tooltip: {
      formatter: p => `<b>${p.value[3]}</b><br/>关联书籍: ${p.value[0]} 本<br/>平均阅读量: ${Number(p.value[1] * 10000).toLocaleString()}`
    },
    grid: { left: 65, right: 30, top: 30, bottom: 50 },
    xAxis: {
      name: '关联书籍数', nameLocation: 'center', nameGap: 32,
      splitLine: { lineStyle: { type: 'dashed', color: '#f0f2f5' } }
    },
    yAxis: {
      name: '平均阅读量(万)', nameLocation: 'center', nameGap: 48,
      splitLine: { lineStyle: { type: 'dashed', color: '#f0f2f5' } }
    },
    series: [{
      type: 'scatter',
      symbolSize: val => Math.max(16, Math.sqrt(val[2] / maxCount) * 60),
      data: items.map((k, i) => ({
        value: [k.count, Math.round((k.avgReads || 0) / 10000 * 10) / 10, k.count, k.keyword],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
            { offset: 0, color: barColors[i % barColors.length] },
            { offset: 1, color: barColors[(i + 3) % barColors.length] }
          ]),
          opacity: 0.85, shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.12)'
        }
      })),
      label: { show: true, formatter: p => p.value[3], fontSize: 11, fontWeight: 600, position: 'top', color: '#555' },
      emphasis: { scale: 1.4, itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0,0,0,0.25)' } }
    }]
  })
}

function initWordcloud() {
  if (!wordcloudRef.value || topKeywords.value.length === 0) return
  if (wordcloudChart) wordcloudChart.dispose()
  wordcloudChart = echarts.init(wordcloudRef.value)

  wordcloudChart.setOption({
    tooltip: { formatter: p => `${p.name}: ${p.value} 本` },
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      sizeRange: [14, 56],
      rotationRange: [-30, 30],
      gridSize: 8,
      textStyle: {
        fontWeight: 'bold',
        color: () => barColors[Math.floor(Math.random() * barColors.length)]
      },
      emphasis: { textStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' } },
      data: topKeywords.value.map(k => ({ name: k.keyword, value: k.count }))
    }]
  })
}

function initFunnel() {
  if (!funnelRef.value || emergingKeywords.value.length === 0) return
  if (funnelChart) funnelChart.dispose()
  funnelChart = echarts.init(funnelRef.value)

  const sorted = [...emergingKeywords.value].sort((a, b) => (b.avgReads || 0) - (a.avgReads || 0)).slice(0, 8)

  funnelChart.setOption({
    tooltip: { formatter: p => `${p.name}<br/>平均阅读量: ${Number(p.value).toLocaleString()}` },
    series: [{
      type: 'funnel',
      left: 60, right: 40, top: 10, bottom: 10,
      minSize: '20%', maxSize: '100%',
      sort: 'descending', gap: 4,
      label: { show: true, position: 'inside', fontSize: 13, fontWeight: 600, color: '#fff' },
      itemStyle: { borderWidth: 0 },
      data: sorted.map((k, i) => ({
        name: k.keyword,
        value: k.avgReads || 0,
        itemStyle: { color: barColors[i % barColors.length] }
      }))
    }]
  })
}

function highlightKeyword(keyword) {
  if (!bubbleChart) return
  bubbleChart.dispatchAction({ type: 'highlight', name: keyword })
  setTimeout(() => bubbleChart.dispatchAction({ type: 'downplay', name: keyword }), 2000)
}

function handleResize() { bubbleChart?.resize(); wordcloudChart?.resize(); funnelChart?.resize() }
onMounted(() => { loadData(); window.addEventListener('resize', handleResize) })
onUnmounted(() => { window.removeEventListener('resize', handleResize); bubbleChart?.dispose(); wordcloudChart?.dispose(); funnelChart?.dispose() })
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.keyword-trend-page { padding: $spacing-lg; background: $bg-page; min-height: calc(100vh - #{$top-nav-height}); }
.page-header { margin-bottom: $spacing-lg; .page-title { font-size: 22px; font-weight: 700; color: $text-primary; margin: 0 0 6px 0; } .page-desc { font-size: 13px; color: $text-secondary; margin: 0; } }
.card-box { background: $bg-white; border-radius: $border-radius-md; box-shadow: $box-shadow-light; padding: $spacing-lg; margin-bottom: $spacing-md; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: $spacing-md; .card-title { font-size: 16px; font-weight: 600; color: $text-primary; } }
.help-icon { color: $text-secondary; cursor: pointer; font-size: 16px; }
.chart-container { width: 100%; height: 440px; }
.chart-container-sm { width: 100%; height: 320px; }

/* 排行卡片 */
.rank-list { display: flex; flex-direction: column; gap: 6px; max-height: 420px; overflow-y: auto; }
.rank-item {
  display: flex; align-items: center; gap: 10px; padding: 8px 10px;
  border-radius: 8px; cursor: pointer; transition: all 0.25s;
  &:hover { background: #f5f7fa; transform: translateX(4px); }
}
.rank-num {
  width: 24px; height: 24px; border-radius: 7px; display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; color: #fff; background: #c0c4cc; flex-shrink: 0;
  &.rank-1 { background: linear-gradient(135deg, #f7971e, #ffd200); }
  &.rank-2 { background: linear-gradient(135deg, #bdc3c7, #95a5a6); }
  &.rank-3 { background: linear-gradient(135deg, #e67e22, #d35400); }
}
.rank-info { flex: 1; min-width: 0; .rank-name { font-size: 13px; font-weight: 600; color: $text-primary; display: block; margin-bottom: 4px; } }
.rank-bar-bg { height: 5px; background: #f0f2f5; border-radius: 3px; overflow: hidden; }
.rank-bar-fill { height: 100%; border-radius: 3px; transition: width 0.8s ease; }
.rank-count { font-size: 12px; color: $text-secondary; font-weight: 500; flex-shrink: 0; white-space: nowrap; }

/* 洞察卡片 */
.insight-list { display: flex; flex-direction: column; gap: 12px; }
.insight-item { display: flex; align-items: flex-start; gap: 8px; font-size: 13px; color: $text-regular; line-height: 1.6; }
.insight-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
</style>
