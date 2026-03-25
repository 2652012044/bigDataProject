<template>
  <div class="big-screen">
    <div class="screen-header">
      <div class="header-bottom-border"></div>
      <span class="title">小说大数据可视化平台</span>
      <span class="header-time">{{ currentTime }}</span>
    </div>

    <!-- 统计概览条 -->
    <div class="stats-summary">
      <div class="stat-item">
        <span class="stat-value">{{ animatedStats.totalNovel }}</span>
        <span class="stat-label">小说总量</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-value">{{ animatedStats.activeUsers }}</span>
        <span class="stat-label">注册用户</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-value">{{ animatedStats.totalComments }}</span>
        <span class="stat-label">评论总数</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-value">{{ animatedStats.avgScore }}</span>
        <span class="stat-label">平均评分</span>
      </div>
    </div>

    <div class="screen-body">
      <!-- 左列 -->
      <div class="screen-col">
        <div class="screen-card">
          <div class="hud-corner tl"></div>
          <div class="hud-corner tr"></div>
          <div class="hud-corner bl"></div>
          <div class="hud-corner br"></div>
          <div class="card-title">热门排行榜</div>
          <div class="card-content rank-list" ref="rankListRef">
            <div class="rank-scroll-wrapper" :style="{ transform: `translateY(-${rankScrollY}px)` }">
              <div v-for="(item, i) in rankList" :key="i" class="rank-item">
                <span class="rank-badge" :class="{ gold: i === 0, silver: i === 1, bronze: i === 2 }">{{ i + 1 }}</span>
                <div class="rank-info">
                  <span class="rank-name">{{ item.bookName }}</span>
                  <div class="rank-bar-bg">
                    <div class="rank-bar-fill" :style="{ width: rankBarWidth(item.readCount) + '%' }"></div>
                  </div>
                </div>
                <span class="rank-heat">{{ formatReads(item.readCount) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="screen-card">
          <div class="hud-corner tl"></div>
          <div class="hud-corner tr"></div>
          <div class="hud-corner bl"></div>
          <div class="hud-corner br"></div>
          <div class="card-title">分类占比</div>
          <div class="card-content" ref="pieChartRef"></div>
        </div>
      </div>

      <!-- 中列 -->
      <div class="screen-col">
        <div class="screen-card">
          <div class="hud-corner tl"></div>
          <div class="hud-corner tr"></div>
          <div class="hud-corner bl"></div>
          <div class="hud-corner br"></div>
          <div class="card-title">分类书籍数量分布</div>
          <div class="card-content" ref="barChartRef"></div>
        </div>
        <div class="screen-card">
          <div class="hud-corner tl"></div>
          <div class="hud-corner tr"></div>
          <div class="hud-corner bl"></div>
          <div class="hud-corner br"></div>
          <div class="card-title">标签词云</div>
          <div class="card-content" ref="wordCloudRef"></div>
        </div>
      </div>

      <!-- 右列 -->
      <div class="screen-col">
        <div class="screen-card">
          <div class="hud-corner tl"></div>
          <div class="hud-corner tr"></div>
          <div class="hud-corner bl"></div>
          <div class="hud-corner br"></div>
          <div class="card-title">情感分析仪表盘</div>
          <div class="card-content sentiment-gauges">
            <div class="gauges-chart-area" ref="gaugeChartRef"></div>
            <div class="sentiment-stats">
              <div class="sentiment-stat">
                <span class="s-dot positive"></span>
                <span class="s-value">{{ sentimentData.positiveRate || 0 }}%</span>
                <span class="s-label">正面</span>
              </div>
              <div class="sentiment-stat">
                <span class="s-dot neutral"></span>
                <span class="s-value">{{ sentimentData.neutralRate || 0 }}%</span>
                <span class="s-label">中性</span>
              </div>
              <div class="sentiment-stat">
                <span class="s-dot negative"></span>
                <span class="s-value">{{ sentimentData.negativeRate || 0 }}%</span>
                <span class="s-label">负面</span>
              </div>
            </div>
          </div>
        </div>
        <div class="screen-card">
          <div class="hud-corner tl"></div>
          <div class="hud-corner tr"></div>
          <div class="hud-corner bl"></div>
          <div class="hud-corner br"></div>
          <div class="card-title">实时动态</div>
          <div class="card-content feed-list" ref="feedListRef">
            <div class="feed-scroll-wrapper" :style="{ transform: `translateY(-${feedScrollY}px)` }">
              <div v-for="(item, i) in feedList" :key="i" class="feed-item">
                <span class="feed-dot" :class="'type-' + (i % 4)"></span>
                <span class="feed-time">{{ item.time }}</span>
                <span class="feed-text">{{ item.text }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-button class="back-btn" type="primary" circle @click="$router.push('/home')">
      <el-icon><Back /></el-icon>
    </el-button>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import { Back } from '@element-plus/icons-vue'
import request from '@/api/index'

const pieChartRef = ref(null)
const barChartRef = ref(null)
const wordCloudRef = ref(null)
const gaugeChartRef = ref(null)
const rankListRef = ref(null)
const feedListRef = ref(null)
let pieChart = null, barChart = null, wordCloudChart = null, gaugeChart = null

const currentTime = ref('')
let timeTimer = null
const rankList = ref([])
const feedList = ref([])
const sentimentData = ref({})

// 自动滚动
const rankScrollY = ref(0)
const feedScrollY = ref(0)
let rankTimer = null
let feedTimer = null

// 数字动画
const animatedStats = reactive({ totalNovel: 0, activeUsers: 0, totalComments: 0, avgScore: '0.0' })
const targetStats = reactive({ totalNovel: 0, activeUsers: 0, totalComments: 0, avgScore: 0 })

function updateTime() {
  currentTime.value = new Date().toLocaleString('zh-CN', { hour12: false })
}

function formatReads(count) {
  const n = Number(count || 0)
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return n.toString()
}

function rankBarWidth(readCount) {
  const max = Math.max(...rankList.value.map(r => Number(r.readCount || 0)), 1)
  return Math.round((Number(readCount || 0) / max) * 100)
}

// 数字递增动画
function animateNumber(key, target, duration = 2000) {
  const start = 0
  const startTime = Date.now()
  const isFloat = key === 'avgScore'

  function step() {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    const current = start + (target - start) * eased

    if (isFloat) {
      animatedStats[key] = current.toFixed(1)
    } else {
      animatedStats[key] = Math.round(current).toLocaleString()
    }

    if (progress < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

// 自动滚动排行榜
function startRankScroll() {
  const itemHeight = 42
  let index = 0
  const maxVisible = 6
  rankTimer = setInterval(() => {
    if (rankList.value.length <= maxVisible) return
    index++
    if (index >= rankList.value.length - maxVisible + 1) index = 0
    rankScrollY.value = index * itemHeight
  }, 3000)
}

// 自动滚动动态
function startFeedScroll() {
  const itemHeight = 40
  let index = 0
  const maxVisible = 6
  feedTimer = setInterval(() => {
    if (feedList.value.length <= maxVisible) return
    index++
    if (index >= feedList.value.length - maxVisible + 1) index = 0
    feedScrollY.value = index * itemHeight
  }, 2500)
}

async function loadBigScreenData() {
  try {
    const res = await request.get('/bigscreen/data')
    const data = res.data || {}

    rankList.value = data.hotBooks || []
    feedList.value = data.feedList || []
    sentimentData.value = data.sentiment || {}

    // 统计数字动画
    const ov = data.overview || {}
    animateNumber('totalNovel', Number(ov.totalNovel || 0))
    animateNumber('activeUsers', Number(ov.activeUsers || 0))
    animateNumber('totalComments', Number(data.sentiment?.total || 0))
    animateNumber('avgScore', Number(ov.averageScore || 0))

    const categoryRank = data.categoryRank || []
    initPie(categoryRank)
    initBar(categoryRank)
    initWordCloud(data.tagCloud || [])

    const posRate = Number(data.sentiment?.positiveRate || 0)
    const neuRate = Number(data.sentiment?.neutralRate || 0)
    const negRate = Number(data.sentiment?.negativeRate || 0)
    initGauge(posRate, neuRate, negRate)

    startRankScroll()
    startFeedScroll()
  } catch (e) {
    initPie([])
    initBar([])
    initWordCloud([])
    initGauge(0, 0, 0)
  }
}

function initPie(categories) {
  if (!pieChartRef.value) return
  pieChart = echarts.init(pieChartRef.value)
  const colors = ['#409eff', '#43e97b', '#e6a23c', '#f56c6c', '#a18cd1', '#73c0de', '#fc8452', '#9a60b4']
  const top8 = categories.slice(0, 8)
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {d}%', backgroundColor: 'rgba(6, 22, 56, 0.9)', borderColor: 'rgba(64, 158, 255, 0.3)', textStyle: { color: '#e0e6ed' } },
    series: [{
      type: 'pie', radius: ['30%', '65%'], center: ['50%', '50%'], roseType: 'radius',
      label: { color: '#8a9bb5', fontSize: 11, formatter: '{b}\n{d}%' },
      labelLine: { lineStyle: { color: 'rgba(64, 158, 255, 0.3)' } },
      itemStyle: { borderColor: 'rgba(6, 22, 56, 0.85)', borderWidth: 2, shadowBlur: 10, shadowColor: 'rgba(64, 158, 255, 0.2)' },
      data: top8.map((c, i) => ({ value: c.bookCount, name: c.categoryName, itemStyle: { color: colors[i % colors.length] } })),
      animationType: 'scale',
      animationEasing: 'elasticOut'
    }]
  })
}

function initBar(categories) {
  if (!barChartRef.value) return
  barChart = echarts.init(barChartRef.value)
  const top10 = categories.slice(0, 10)
  barChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, backgroundColor: 'rgba(6, 22, 56, 0.9)', borderColor: 'rgba(64, 158, 255, 0.3)', textStyle: { color: '#e0e6ed' } },
    grid: { left: 80, right: 30, top: 10, bottom: 30 },
    xAxis: { type: 'value', show: false },
    yAxis: {
      type: 'category', data: top10.map(c => c.categoryName).reverse(),
      axisLabel: { color: '#8a9bb5', fontSize: 12 },
      axisLine: { lineStyle: { color: 'rgba(64, 158, 255, 0.3)' } },
      axisTick: { show: false }
    },
    series: [{
      type: 'bar', barWidth: 14,
      data: top10.map(c => c.bookCount).reverse(),
      itemStyle: {
        borderRadius: [0, 4, 4, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#409eff' },
          { offset: 0.5, color: '#66b1ff' },
          { offset: 1, color: '#43e97b' }
        ]),
        shadowBlur: 8,
        shadowColor: 'rgba(64, 158, 255, 0.3)'
      },
      label: { show: true, position: 'right', color: '#8a9bb5', fontSize: 11 },
      animationDelay: idx => idx * 80
    }]
  })
}

function initWordCloud(tags) {
  if (!wordCloudRef.value) return
  wordCloudChart = echarts.init(wordCloudRef.value)
  const wcColors = ['#409eff', '#66b1ff', '#43e97b', '#e6a23c', '#a18cd1', '#73c0de', '#fc8452', '#f56c6c']
  wordCloudChart.setOption({
    series: [{
      type: 'wordCloud', shape: 'circle', sizeRange: [14, 44], rotationRange: [-30, 30], gridSize: 8,
      textStyle: {
        fontWeight: 'bold',
        color: () => wcColors[Math.floor(Math.random() * wcColors.length)],
        textShadowBlur: 6,
        textShadowColor: 'rgba(64, 158, 255, 0.3)'
      },
      data: tags.slice(0, 50)
    }]
  })
}

function initGauge(posRate, neuRate, negRate) {
  if (!gaugeChartRef.value) return
  gaugeChart = echarts.init(gaugeChartRef.value)
  gaugeChart.setOption({
    series: [
      {
        type: 'gauge', center: ['50%', '55%'], radius: '75%',
        startAngle: 200, endAngle: -20,
        min: 0, max: 100,
        axisLine: {
          lineStyle: {
            width: 20,
            color: [[0.3, '#f56c6c'], [0.5, '#e6a23c'], [0.7, '#409eff'], [1, '#43e97b']]
          }
        },
        pointer: {
          itemStyle: { color: '#409eff' },
          length: '55%',
          width: 6,
          shadowBlur: 10,
          shadowColor: 'rgba(64, 158, 255, 0.5)'
        },
        axisTick: { distance: -20, length: 6, lineStyle: { color: 'rgba(255,255,255,0.3)', width: 1 } },
        splitLine: { distance: -20, length: 20, lineStyle: { color: 'rgba(255,255,255,0.3)', width: 2 } },
        axisLabel: { color: '#8a9bb5', distance: 28, fontSize: 11 },
        detail: {
          valueAnimation: true,
          formatter: '{value}%',
          color: '#43e97b',
          fontSize: 32,
          fontWeight: 'bold',
          offsetCenter: [0, '60%'],
          textShadowBlur: 12,
          textShadowColor: 'rgba(67, 233, 123, 0.4)'
        },
        title: { offsetCenter: [0, '82%'], fontSize: 14, color: '#8a9bb5' },
        data: [{ value: posRate, name: '正面情感率' }],
        animationDuration: 2000,
        animationEasing: 'bounceOut'
      }
    ]
  })
}

const handleResize = () => {
  pieChart?.resize()
  barChart?.resize()
  wordCloudChart?.resize()
  gaugeChart?.resize()
}

onMounted(() => {
  updateTime()
  timeTimer = setInterval(updateTime, 1000)
  loadBigScreenData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  clearInterval(timeTimer)
  clearInterval(rankTimer)
  clearInterval(feedTimer)
  window.removeEventListener('resize', handleResize)
  pieChart?.dispose()
  barChart?.dispose()
  wordCloudChart?.dispose()
  gaugeChart?.dispose()
})
</script>

<style lang="scss">
@use '@/assets/styles/bigscreen.scss';
</style>
