<template>
  <div class="big-screen">
    <div class="screen-header">
      <span class="title">小说大数据可视化平台</span>
      <span class="header-time">{{ currentTime }}</span>
    </div>
    <div class="screen-body">
      <!-- 左列 -->
      <div class="screen-col">
        <div class="screen-card">
          <div class="card-title">热门排行榜</div>
          <div class="card-content rank-list">
            <div v-for="(item, i) in rankList" :key="i" class="rank-item">
              <span class="rank-num" :class="{ top3: i < 3 }">{{ i + 1 }}</span>
              <span class="rank-name">{{ item.bookName }}</span>
              <span class="rank-heat">{{ Number(item.readCount).toLocaleString() }}</span>
            </div>
          </div>
        </div>
        <div class="screen-card">
          <div class="card-title">分类占比</div>
          <div class="card-content" ref="pieChartRef"></div>
        </div>
      </div>

      <!-- 中列 -->
      <div class="screen-col">
        <div class="screen-card">
          <div class="card-title">分类书籍数量分布</div>
          <div class="card-content" ref="barChartRef"></div>
        </div>
        <div class="screen-card">
          <div class="card-title">标签词云</div>
          <div class="card-content" ref="wordCloudRef"></div>
        </div>
      </div>

      <!-- 右列 -->
      <div class="screen-col">
        <div class="screen-card">
          <div class="card-title">情感分析仪表盘</div>
          <div class="card-content" ref="gaugeChartRef"></div>
        </div>
        <div class="screen-card">
          <div class="card-title">实时动态</div>
          <div class="card-content feed-list">
            <div v-for="(item, i) in feedList" :key="i" class="feed-item">
              <span class="feed-time">{{ item.time }}</span>
              <span class="feed-text">{{ item.text }}</span>
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
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import { Back } from '@element-plus/icons-vue'
import request from '@/api/index'

const pieChartRef = ref(null)
const barChartRef = ref(null)
const wordCloudRef = ref(null)
const gaugeChartRef = ref(null)
let pieChart = null, barChart = null, wordCloudChart = null, gaugeChart = null

const currentTime = ref('')
let timeTimer = null
const rankList = ref([])
const feedList = ref([])

function updateTime() {
  currentTime.value = new Date().toLocaleString('zh-CN', { hour12: false })
}

async function loadBigScreenData() {
  try {
    const res = await request.get('/bigscreen/data')
    const data = res.data || {}

    // 热门排行
    rankList.value = data.hotBooks || []

    // 实时动态
    feedList.value = data.feedList || []

    // 分类占比饼图
    const categoryRank = data.categoryRank || []
    initPie(categoryRank)

    // 分类柱状图
    initBar(categoryRank)

    // 标签词云
    const tagCloud = data.tagCloud || []
    initWordCloud(tagCloud)

    // 情感仪表盘
    const sentiment = data.sentiment || {}
    const posRate = sentiment.positiveRate || 0
    initGauge(posRate)
  } catch (e) {
    initPie([])
    initBar([])
    initWordCloud([])
    initGauge(0)
  }
}

function initPie(categories) {
  if (!pieChartRef.value) return
  pieChart = echarts.init(pieChartRef.value)
  const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#a18cd1', '#909399', '#1abc9c', '#e67e22']
  const top8 = categories.slice(0, 8)
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
    series: [{
      type: 'pie', radius: ['35%', '65%'], center: ['50%', '50%'],
      label: { color: '#8a9bb5', fontSize: 12 },
      itemStyle: { borderColor: 'rgba(6,30,65,0.85)', borderWidth: 2 },
      data: top8.map((c, i) => ({ value: c.bookCount, name: c.categoryName, itemStyle: { color: colors[i % colors.length] } }))
    }]
  })
}

function initBar(categories) {
  if (!barChartRef.value) return
  barChart = echarts.init(barChartRef.value)
  const top10 = categories.slice(0, 10)
  barChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 80, right: 30, top: 10, bottom: 30 },
    xAxis: { type: 'value', show: false },
    yAxis: { type: 'category', data: top10.map(c => c.categoryName).reverse(), axisLabel: { color: '#8a9bb5', fontSize: 12 }, axisLine: { lineStyle: { color: 'rgba(64,158,255,0.3)' } } },
    series: [{
      type: 'bar', barWidth: 14,
      data: top10.map(c => c.bookCount).reverse(),
      itemStyle: { borderRadius: [0, 4, 4, 0], color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#409eff' }, { offset: 1, color: '#66b1ff' }]) },
      label: { show: true, position: 'right', color: '#8a9bb5', fontSize: 11 }
    }]
  })
}

function initWordCloud(tags) {
  if (!wordCloudRef.value) return
  wordCloudChart = echarts.init(wordCloudRef.value)
  wordCloudChart.setOption({
    series: [{
      type: 'wordCloud', shape: 'circle', sizeRange: [12, 42], rotationRange: [-45, 45], gridSize: 6,
      textStyle: { fontWeight: 'bold', color: () => ['#409eff', '#66b1ff', '#43e97b', '#e6a23c', '#a18cd1'][Math.floor(Math.random() * 5)] },
      data: tags.slice(0, 40)
    }]
  })
}

function initGauge(posRate) {
  if (!gaugeChartRef.value) return
  gaugeChart = echarts.init(gaugeChartRef.value)
  gaugeChart.setOption({
    series: [{
      type: 'gauge', center: ['50%', '60%'], radius: '80%',
      axisLine: { lineStyle: { width: 16, color: [[0.3, '#f56c6c'], [0.7, '#e6a23c'], [1, '#67c23a']] } },
      pointer: { itemStyle: { color: '#409eff' }, length: '60%', width: 6 },
      axisTick: { distance: -16, length: 6, lineStyle: { color: '#fff', width: 1 } },
      splitLine: { distance: -16, length: 16, lineStyle: { color: '#fff', width: 2 } },
      axisLabel: { color: '#8a9bb5', distance: 24, fontSize: 11 },
      detail: { valueAnimation: true, formatter: '{value}%', color: '#409eff', fontSize: 28, fontWeight: 'bold', offsetCenter: [0, '70%'] },
      title: { offsetCenter: [0, '90%'], fontSize: 14, color: '#8a9bb5' },
      data: [{ value: posRate, name: '正面情感率' }]
    }]
  })
}

const handleResize = () => { pieChart?.resize(); barChart?.resize(); wordCloudChart?.resize(); gaugeChart?.resize() }

onMounted(() => {
  updateTime()
  timeTimer = setInterval(updateTime, 1000)
  loadBigScreenData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  clearInterval(timeTimer)
  window.removeEventListener('resize', handleResize)
  pieChart?.dispose(); barChart?.dispose(); wordCloudChart?.dispose(); gaugeChart?.dispose()
})
</script>

<style lang="scss">
@use '@/assets/styles/bigscreen.scss';

.header-time { position: absolute; right: 24px; font-size: 14px; color: #8a9bb5; }
.screen-header { position: relative; }
.screen-col { display: flex; flex-direction: column; gap: 12px; .screen-card { flex: 1; } }
.rank-list {
  overflow: hidden;
  .rank-item { display: flex; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(64, 158, 255, 0.1); }
  .rank-num { width: 22px; height: 22px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: #8a9bb5; margin-right: 10px; &.top3 { color: #ffd700; } }
  .rank-name { flex: 1; font-size: 13px; color: #e0e6ed; }
  .rank-heat { font-size: 12px; color: #409eff; font-weight: 600; }
}
.feed-list {
  overflow-y: auto;
  .feed-item { display: flex; gap: 10px; padding: 8px 0; border-bottom: 1px solid rgba(64, 158, 255, 0.1); }
  .feed-time { font-size: 12px; color: #409eff; flex-shrink: 0; min-width: 40px; }
  .feed-text { font-size: 13px; color: #e0e6ed; }
}
.back-btn { position: fixed; top: 16px; right: 16px; z-index: 100; }
</style>
