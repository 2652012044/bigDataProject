<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">类型统计</h2>
      <p class="page-desc">多维度对比各类型小说的数量、评分、字数、完结率与阅读量</p>
    </div>

    <!-- 顶部指标卡片 -->
    <div class="stat-cards">
      <div class="stat-card" v-for="card in statCards" :key="card.label">
        <div class="stat-icon" :style="{ background: card.color }">
          <el-icon :size="22"><component :is="card.icon" /></el-icon>
        </div>
        <div class="stat-body">
          <span class="stat-value">{{ card.value }}</span>
          <span class="stat-label">{{ card.label }}</span>
        </div>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 散点气泡图：评分 vs 字数 vs 数量 -->
      <el-col :span="14">
        <div class="card-box">
          <div class="card-box-header">
            <span class="card-box-title">类型多维对比（评分 × 字数 × 数量）</span>
            <el-tooltip content="X轴=平均评分，Y轴=平均字数(万)，气泡大小=书籍数量" placement="top">
              <el-icon class="help-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
          <div ref="bubbleRef" class="chart-container"></div>
        </div>
      </el-col>

      <!-- 极坐标多维雷达 -->
      <el-col :span="10">
        <div class="card-box">
          <div class="card-box-header">
            <span class="card-box-title">类型能力雷达</span>
            <el-select v-model="radarSelected" multiple :max-collapse-tags="2" collapse-tags placeholder="选择对比类型" size="small" style="width:220px">
              <el-option v-for="t in typeList" :key="t.name" :label="t.name" :value="t.name" />
            </el-select>
          </div>
          <div ref="radarRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- 矩形树图 -->
      <el-col :span="10">
        <div class="card-box">
          <div class="card-box-header">
            <span class="card-box-title">类型分布矩形树图</span>
          </div>
          <div ref="treemapRef" class="chart-container"></div>
        </div>
      </el-col>

      <!-- 详细数据表 -->
      <el-col :span="14">
        <div class="card-box">
          <div class="card-box-header">
            <span class="card-box-title">各类型详细指标</span>
          </div>
          <div class="detail-table">
            <div class="table-header">
              <span class="col-rank">#</span>
              <span class="col-name">类型</span>
              <span class="col-num">数量</span>
              <span class="col-score">平均评分</span>
              <span class="col-words">平均字数</span>
              <span class="col-rate">完结率</span>
              <span class="col-bar">阅读量占比</span>
            </div>
            <div v-for="(item, idx) in typeList" :key="item.name" class="table-row" :class="{ 'row-even': idx % 2 === 0 }">
              <span class="col-rank">
                <span class="rank-badge" :class="'rank-' + (idx + 1)" v-if="idx < 3">{{ idx + 1 }}</span>
                <span v-else>{{ idx + 1 }}</span>
              </span>
              <span class="col-name fw">{{ item.name }}</span>
              <span class="col-num">{{ item.count.toLocaleString() }}</span>
              <span class="col-score">
                <span class="score-dot" :style="{ background: scoreColor(item.avgScore) }"></span>
                {{ item.avgScore }}
              </span>
              <span class="col-words">{{ formatWords(item.avgWordCount) }}</span>
              <span class="col-rate">
                <div class="mini-bar-bg">
                  <div class="mini-bar-fill" :style="{ width: item.completedRate + '%', background: rateColor(item.completedRate) }"></div>
                </div>
                <span class="rate-text">{{ item.completedRate }}%</span>
              </span>
              <span class="col-bar">
                <div class="read-bar-bg">
                  <div class="read-bar-fill" :style="{ width: item.readPercent + '%', background: typeColors[idx % typeColors.length] }"></div>
                </div>
              </span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { QuestionFilled, DataLine, TrendCharts, Medal, Reading } from '@element-plus/icons-vue'
import request from '@/api/index'

const typeColors = [
  '#667eea', '#764ba2', '#43e97b', '#f093fb', '#4facfe',
  '#fa709a', '#fccb90', '#a18cd1', '#38f9d7', '#fee140',
  '#5470c6', '#91cc75', '#ee6666', '#73c0de', '#fc8452'
]

const bubbleRef = ref(null)
const radarRef = ref(null)
const treemapRef = ref(null)
let bubbleChart = null, radarChart = null, treemapChart = null

const typeList = ref([])
const radarSelected = ref([])
let grandTotal = 0
let maxReads = 0

const statCards = computed(() => {
  if (typeList.value.length === 0) return []
  const best = [...typeList.value].sort((a, b) => b.avgScore - a.avgScore)[0]
  const most = [...typeList.value].sort((a, b) => b.count - a.count)[0]
  const highRate = [...typeList.value].sort((a, b) => b.completedRate - a.completedRate)[0]
  return [
    { label: '分类总数', value: typeList.value.length, icon: 'DataLine', color: 'linear-gradient(135deg,#667eea,#764ba2)' },
    { label: '书籍总量', value: grandTotal.toLocaleString(), icon: 'Reading', color: 'linear-gradient(135deg,#43e97b,#38f9d7)' },
    { label: '最高评分类型', value: `${best.name} (${best.avgScore})`, icon: 'Medal', color: 'linear-gradient(135deg,#f093fb,#f5576c)' },
    { label: '最高完结率', value: `${highRate.name} (${highRate.completedRate}%)`, icon: 'TrendCharts', color: 'linear-gradient(135deg,#4facfe,#00f2fe)' },
  ]
})

function scoreColor(s) { return s >= 8 ? '#67c23a' : s >= 6 ? '#409eff' : s >= 4 ? '#e6a23c' : '#f56c6c' }
function rateColor(r) { return r >= 60 ? '#67c23a' : r >= 30 ? '#e6a23c' : '#f56c6c' }
function formatWords(w) { return w >= 10000 ? (w / 10000).toFixed(1) + '万' : w.toLocaleString() }

async function loadTypeStats() {
  try {
    const res = await request.get('/analysis/type-stats')
    const data = res.data || {}
    const types = data.types || []
    grandTotal = data.totalBooks || 0
    const totalReads = types.reduce((s, t) => s + (t.totalReads || 0), 0)
    maxReads = Math.max(...types.map(t => t.totalReads || 0))

    typeList.value = types.map(t => ({
      ...t,
      readPercent: totalReads > 0 ? Math.round((t.totalReads || 0) * 100 / totalReads) : 0
    }))

    // 默认选中前3个做雷达对比
    radarSelected.value = types.slice(0, 3).map(t => t.name)

    initBubbleChart()
    initRadarChart()
    initTreemap()
  } catch (e) { /* keep empty */ }
}

function initBubbleChart() {
  if (!bubbleRef.value || typeList.value.length === 0) return
  if (bubbleChart) bubbleChart.dispose()
  bubbleChart = echarts.init(bubbleRef.value)

  const maxCount = Math.max(...typeList.value.map(t => t.count))

  bubbleChart.setOption({
    tooltip: {
      formatter: p => `<b>${p.value[3]}</b><br/>平均评分: ${p.value[0]}<br/>平均字数: ${formatWords(p.value[1] * 10000)}<br/>书籍数量: ${p.value[2]}`
    },
    grid: { left: 60, right: 30, top: 30, bottom: 45 },
    xAxis: {
      name: '平均评分', nameLocation: 'center', nameGap: 30,
      min: v => Math.floor(v.min * 10) / 10 - 0.2,
      splitLine: { lineStyle: { type: 'dashed', color: '#f0f2f5' } },
      axisLabel: { fontSize: 12 }
    },
    yAxis: {
      name: '平均字数(万)', nameLocation: 'center', nameGap: 40,
      splitLine: { lineStyle: { type: 'dashed', color: '#f0f2f5' } },
      axisLabel: { fontSize: 12 }
    },
    series: [{
      type: 'scatter',
      symbolSize: val => Math.max(20, Math.sqrt(val[2] / maxCount) * 80),
      data: typeList.value.map((t, i) => ({
        value: [t.avgScore, Math.round((t.avgWordCount || 0) / 10000 * 10) / 10, t.count, t.name],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
            { offset: 0, color: typeColors[i % typeColors.length] },
            { offset: 1, color: typeColors[(i + 1) % typeColors.length] }
          ]),
          opacity: 0.85,
          shadowBlur: 12,
          shadowColor: 'rgba(0,0,0,0.15)'
        }
      })),
      label: {
        show: true,
        formatter: p => p.value[3],
        fontSize: 11, fontWeight: 600, color: '#333',
        position: 'top'
      },
      emphasis: {
        scale: 1.3,
        itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0,0,0,0.3)' }
      }
    }]
  })
}

function initRadarChart() {
  if (!radarRef.value || typeList.value.length === 0) return
  if (radarChart) radarChart.dispose()
  radarChart = echarts.init(radarRef.value)
  updateRadar()
}

function updateRadar() {
  if (!radarChart || radarSelected.value.length === 0) return
  const selected = typeList.value.filter(t => radarSelected.value.includes(t.name))
  if (selected.length === 0) return

  const maxScore = 10
  const maxWords = Math.max(...typeList.value.map(t => t.avgWordCount || 0))
  const maxCount = Math.max(...typeList.value.map(t => t.count))
  const maxRate = 100
  const maxR = maxReads

  radarChart.setOption({
    tooltip: {},
    legend: { bottom: 0, data: selected.map(s => s.name), textStyle: { fontSize: 12 } },
    radar: {
      indicator: [
        { name: '平均评分', max: maxScore },
        { name: '平均字数', max: maxWords },
        { name: '书籍数量', max: maxCount },
        { name: '完结率', max: maxRate },
        { name: '总阅读量', max: maxR }
      ],
      radius: '60%',
      axisName: { color: '#606266', fontSize: 12 },
      splitArea: { areaStyle: { color: ['rgba(102,126,234,0.05)', 'rgba(102,126,234,0.1)'] } }
    },
    series: [{
      type: 'radar',
      data: selected.map((s, i) => ({
        name: s.name,
        value: [s.avgScore, s.avgWordCount || 0, s.count, s.completedRate || 0, s.totalReads || 0],
        areaStyle: { opacity: 0.15 },
        lineStyle: { width: 2.5 },
        itemStyle: { color: typeColors[typeList.value.indexOf(s) % typeColors.length] },
        symbol: 'circle',
        symbolSize: 6
      }))
    }]
  }, true)
}

function initTreemap() {
  if (!treemapRef.value || typeList.value.length === 0) return
  if (treemapChart) treemapChart.dispose()
  treemapChart = echarts.init(treemapRef.value)

  treemapChart.setOption({
    tooltip: {
      formatter: p => {
        const pct = grandTotal > 0 ? ((p.value / grandTotal) * 100).toFixed(1) : 0
        return `<b>${p.name}</b><br/>数量: ${p.value.toLocaleString()} 部<br/>占比: ${pct}%`
      }
    },
    series: [{
      type: 'treemap', width: '95%', height: '90%', top: '5%', left: '2.5%',
      roam: false, nodeClick: false, breadcrumb: { show: false },
      label: {
        show: true, formatter: p => {
          const pct = grandTotal > 0 ? ((p.value / grandTotal) * 100).toFixed(1) : 0
          return `{name|${p.name}}\n{val|${p.value.toLocaleString()}部}\n{pct|${pct}%}`
        },
        rich: {
          name: { fontSize: 15, fontWeight: 'bold', color: '#fff', lineHeight: 26 },
          val: { fontSize: 12, color: 'rgba(255,255,255,0.85)', lineHeight: 20 },
          pct: { fontSize: 18, fontWeight: 'bold', color: '#fff', lineHeight: 26 }
        },
        align: 'center', verticalAlign: 'middle'
      },
      itemStyle: { borderRadius: 6, gapWidth: 3 },
      emphasis: { itemStyle: { shadowBlur: 15, shadowColor: 'rgba(0,0,0,0.3)' } },
      levels: [{ itemStyle: { borderColor: '#fff', borderWidth: 3, gapWidth: 3 } }],
      data: typeList.value.map((t, i) => ({
        name: t.name, value: t.count,
        itemStyle: { color: typeColors[i % typeColors.length] }
      }))
    }]
  })
}

function handleResize() { bubbleChart?.resize(); radarChart?.resize(); treemapChart?.resize() }

watch(radarSelected, () => updateRadar())

onMounted(() => { loadTypeStats(); window.addEventListener('resize', handleResize) })
onUnmounted(() => { window.removeEventListener('resize', handleResize); bubbleChart?.dispose(); radarChart?.dispose(); treemapChart?.dispose() })
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.page-container { padding: $spacing-lg; min-height: 100%; }
.page-header { margin-bottom: $spacing-lg; .page-title { font-size: 22px; font-weight: 600; color: $text-primary; margin: 0 0 $spacing-xs 0; } .page-desc { font-size: 14px; color: $text-secondary; margin: 0; } }

.stat-cards {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: $spacing-lg;

  .stat-card {
    background: $bg-white; border-radius: 14px; box-shadow: $box-shadow-light; padding: 18px 20px;
    display: flex; align-items: center; gap: 14px; transition: transform 0.3s;
    &:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
  }

  .stat-icon { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; color: #fff; flex-shrink: 0; }
  .stat-body { display: flex; flex-direction: column; min-width: 0; }
  .stat-value { font-size: 18px; font-weight: 700; color: $text-primary; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .stat-label { font-size: 12px; color: $text-secondary; margin-top: 2px; }
}

.card-box {
  background: $bg-white; border-radius: $border-radius-md; box-shadow: $box-shadow-light; padding: $spacing-lg; margin-bottom: $spacing-lg;
  .card-box-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: $spacing-md; .card-box-title { font-size: 16px; font-weight: 600; color: $text-primary; } }
}

.help-icon { color: $text-secondary; cursor: pointer; font-size: 16px; }
.chart-container { width: 100%; height: 400px; }

/* 详细数据表 */
.detail-table { font-size: 13px; }

.table-header {
  display: flex; align-items: center; padding: 10px 12px; border-bottom: 2px solid $border-light;
  font-weight: 600; color: $text-secondary; font-size: 12px; text-transform: uppercase;
}

.table-row {
  display: flex; align-items: center; padding: 11px 12px; border-bottom: 1px solid #f5f5f5;
  transition: background 0.2s;
  &:hover { background: #f7f8fb; }
  &.row-even { background: #fafbfd; &:hover { background: #f0f2f8; } }
}

.col-rank { width: 36px; text-align: center; flex-shrink: 0; color: $text-secondary; }
.col-name { width: 80px; flex-shrink: 0; color: $text-primary; &.fw { font-weight: 600; } }
.col-num { width: 60px; text-align: right; flex-shrink: 0; font-weight: 500; }
.col-score { width: 80px; text-align: center; flex-shrink: 0; display: flex; align-items: center; justify-content: center; gap: 5px; font-weight: 600; }
.col-words { width: 80px; text-align: right; flex-shrink: 0; color: $text-secondary; }
.col-rate { width: 110px; flex-shrink: 0; display: flex; align-items: center; gap: 6px; }
.col-bar { flex: 1; min-width: 0; }

.rank-badge {
  display: inline-flex; width: 22px; height: 22px; border-radius: 6px; align-items: center; justify-content: center;
  color: #fff; font-size: 11px; font-weight: 700;
  &.rank-1 { background: linear-gradient(135deg, #f7971e, #ffd200); }
  &.rank-2 { background: linear-gradient(135deg, #bdc3c7, #95a5a6); }
  &.rank-3 { background: linear-gradient(135deg, #e67e22, #d35400); }
}

.score-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

.mini-bar-bg { width: 50px; height: 6px; background: #f0f2f5; border-radius: 3px; overflow: hidden; }
.mini-bar-fill { height: 100%; border-radius: 3px; transition: width 0.6s ease; }
.rate-text { font-size: 12px; color: $text-secondary; min-width: 36px; }

.read-bar-bg { width: 100%; height: 8px; background: #f0f2f5; border-radius: 4px; overflow: hidden; }
.read-bar-fill { height: 100%; border-radius: 4px; transition: width 0.8s ease; }

@media (max-width: 1200px) {
  .stat-cards { grid-template-columns: repeat(2, 1fr); }
}
</style>
