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
          <div class="card-content rank-list" ref="rankListRef">
            <div v-for="(item, i) in rankList" :key="i" class="rank-item" :style="{ transform: `translateY(${rankOffset}px)` }">
              <span class="rank-num" :class="{ top3: i < 3 }">{{ i + 1 }}</span>
              <span class="rank-name">{{ item.name }}</span>
              <span class="rank-heat">{{ item.heat.toLocaleString() }}</span>
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
          <div class="card-title">类型趋势河流图</div>
          <div class="card-content" ref="riverChartRef"></div>
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

const pieChartRef = ref(null)
const riverChartRef = ref(null)
const wordCloudRef = ref(null)
const gaugeChartRef = ref(null)
let pieChart = null, riverChart = null, wordCloudChart = null, gaugeChart = null

const currentTime = ref('')
let timeTimer = null
let rankTimer = null
let feedTimer = null
const rankOffset = ref(0)

const rankList = ref([
  { name: '斗破苍穹', heat: 98523 }, { name: '完美世界', heat: 87412 },
  { name: '遮天', heat: 76891 }, { name: '诡秘之主', heat: 65234 },
  { name: '大奉打更人', heat: 54876 }, { name: '夜的命名术', heat: 48321 },
  { name: '深海余烬', heat: 42156 }, { name: '道诡异仙', heat: 38790 },
  { name: '家族修仙', heat: 35421 }, { name: '星门', heat: 31245 }
])

const feedList = ref([
  { time: '10:23', text: '《斗破苍穹》更新了第2156章' },
  { time: '10:21', text: '用户 书虫小王 收藏了《完美世界》' },
  { time: '10:18', text: '《道诡异仙》新增1283条评论' },
  { time: '10:15', text: '用户 夜读者 给《遮天》打了5星' },
  { time: '10:12', text: '《深海余烬》更新了第892章' },
  { time: '10:08', text: '新用户 追更达人 完成注册' },
  { time: '10:05', text: '《诡秘之主》进入热搜榜前三' },
  { time: '10:01', text: '用户 老书虫 评论了《大奉打更人》' }
])

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', { hour12: false })
}

const darkTextStyle = { color: '#8a9bb5', fontSize: 12 }

function initPie() {
  if (!pieChartRef.value) return
  pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
    series: [{
      type: 'pie', radius: ['35%', '65%'], center: ['50%', '50%'],
      label: { color: '#8a9bb5', fontSize: 12 },
      itemStyle: { borderColor: 'rgba(6,30,65,0.85)', borderWidth: 2 },
      data: [
        { value: 30, name: '玄幻', itemStyle: { color: '#409eff' } },
        { value: 22, name: '都市', itemStyle: { color: '#67c23a' } },
        { value: 18, name: '仙侠', itemStyle: { color: '#e6a23c' } },
        { value: 12, name: '科幻', itemStyle: { color: '#f56c6c' } },
        { value: 10, name: '言情', itemStyle: { color: '#a18cd1' } },
        { value: 8, name: '其他', itemStyle: { color: '#909399' } }
      ]
    }]
  })
}

function initRiver() {
  if (!riverChartRef.value) return
  riverChart = echarts.init(riverChartRef.value)
  const types = ['玄幻', '都市', '仙侠', '科幻', '言情']
  const data = []
  for (let m = 1; m <= 12; m++) {
    const month = `2025/${m}`
    types.forEach((t, i) => {
      data.push([month, Math.floor(200 + Math.random() * 300 + i * 50), t])
    })
  }
  riverChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'line' } },
    singleAxis: { type: 'category', bottom: 30, top: 20, axisLabel: { color: '#8a9bb5' }, axisLine: { lineStyle: { color: 'rgba(64,158,255,0.3)' } } },
    series: [{ type: 'themeRiver', data, label: { show: false }, emphasis: { itemStyle: { shadowBlur: 10 } },
      color: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#a18cd1']
    }]
  })
}

function initWordCloud() {
  if (!wordCloudRef.value) return
  wordCloudChart = echarts.init(wordCloudRef.value)
  const words = [
    { name: '穿越', value: 800 }, { name: '重生', value: 750 }, { name: '系统', value: 700 },
    { name: '修仙', value: 680 }, { name: '异能', value: 600 }, { name: '末日', value: 550 },
    { name: '宫斗', value: 500 }, { name: '热血', value: 480 }, { name: '冒险', value: 460 },
    { name: '校园', value: 440 }, { name: '升级', value: 420 }, { name: '复仇', value: 400 },
    { name: '星际', value: 380 }, { name: '甜宠', value: 360 }, { name: '权谋', value: 340 }
  ]
  wordCloudChart.setOption({
    series: [{ type: 'wordCloud', shape: 'circle', sizeRange: [12, 42], rotationRange: [-45, 45], gridSize: 6,
      textStyle: { fontWeight: 'bold', color: () => ['#409eff', '#66b1ff', '#43e97b', '#e6a23c', '#a18cd1'][Math.floor(Math.random() * 5)] },
      data: words
    }]
  })
}

function initGauge() {
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
      data: [{ value: 72, name: '正面情感率' }]
    }]
  })
}

const handleResize = () => {
  pieChart?.resize(); riverChart?.resize(); wordCloudChart?.resize(); gaugeChart?.resize()
}

onMounted(() => {
  updateTime()
  timeTimer = setInterval(updateTime, 1000)
  initPie(); initRiver(); initWordCloud(); initGauge()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  clearInterval(timeTimer); clearInterval(rankTimer); clearInterval(feedTimer)
  window.removeEventListener('resize', handleResize)
  pieChart?.dispose(); riverChart?.dispose(); wordCloudChart?.dispose(); gaugeChart?.dispose()
})
</script>

<style lang="scss">
@use '@/assets/styles/bigscreen.scss';

.header-time {
  position: absolute;
  right: 24px;
  font-size: 14px;
  color: #8a9bb5;
}

.screen-header { position: relative; }

.screen-col {
  display: flex;
  flex-direction: column;
  gap: 12px;

  .screen-card { flex: 1; }
}

.rank-list {
  overflow: hidden;

  .rank-item {
    display: flex;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid rgba(64, 158, 255, 0.1);
    transition: transform 0.5s;
  }

  .rank-num {
    width: 22px;
    height: 22px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
    color: #8a9bb5;
    margin-right: 10px;

    &.top3 { color: #ffd700; }
  }

  .rank-name {
    flex: 1;
    font-size: 13px;
    color: #e0e6ed;
  }

  .rank-heat {
    font-size: 12px;
    color: #409eff;
    font-weight: 600;
  }
}

.feed-list {
  overflow-y: auto;

  .feed-item {
    display: flex;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid rgba(64, 158, 255, 0.1);
  }

  .feed-time {
    font-size: 12px;
    color: #409eff;
    flex-shrink: 0;
    min-width: 40px;
  }

  .feed-text {
    font-size: 13px;
    color: #e0e6ed;
  }
}

.back-btn {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 100;
}
</style>
