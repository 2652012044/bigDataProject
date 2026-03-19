<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">主题分析</h2>
      <p class="page-desc">基于NLP文本聚类的小说主题分布与关联分析</p>
    </div>

    <el-row :gutter="20">
      <!-- 左侧：气泡图 -->
      <el-col :span="15">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="card-header-title">主题聚类气泡图</span>
              <span class="card-header-hint">气泡大小代表相关小说数量，点击查看详情</span>
            </div>
          </template>
          <div ref="bubbleChartRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 右侧：主题详情面板 -->
      <el-col :span="9">
        <el-card shadow="never" class="detail-card">
          <template #header>
            <div class="card-header">
              <span class="card-header-title">主题详情</span>
            </div>
          </template>

          <!-- 未选中状态 -->
          <div v-if="!selectedTopic" class="empty-detail">
            <el-empty description="点击左侧气泡查看主题详情" :image-size="120" />
          </div>

          <!-- 选中状态 -->
          <div v-else class="topic-detail">
            <div class="topic-header">
              <h3 class="topic-name">{{ selectedTopic.name }}</h3>
              <el-tag :type="selectedTopic.trend === '上升' ? 'success' : selectedTopic.trend === '下降' ? 'danger' : 'info'" size="small">
                {{ selectedTopic.trend }}趋势
              </el-tag>
            </div>

            <el-descriptions :column="2" border size="small" class="topic-stats">
              <el-descriptions-item label="相关小说">{{ selectedTopic.novelCount }} 部</el-descriptions-item>
              <el-descriptions-item label="总字数">{{ selectedTopic.totalWords }}亿字</el-descriptions-item>
              <el-descriptions-item label="平均评分">{{ selectedTopic.avgRating }} 分</el-descriptions-item>
              <el-descriptions-item label="读者占比">{{ selectedTopic.readerPercent }}%</el-descriptions-item>
            </el-descriptions>

            <div class="topic-desc">
              <h4>主题描述</h4>
              <p>{{ selectedTopic.description }}</p>
            </div>

            <div class="topic-keywords">
              <h4>核心关键词</h4>
              <div class="keyword-tags">
                <el-tag
                  v-for="kw in selectedTopic.keywords"
                  :key="kw"
                  size="small"
                  effect="plain"
                  class="keyword-tag"
                >
                  {{ kw }}
                </el-tag>
              </div>
            </div>

            <div class="top-novels">
              <h4>代表作品</h4>
              <div
                v-for="novel in selectedTopic.topNovels"
                :key="novel.title"
                class="novel-item"
              >
                <div class="novel-info">
                  <span class="novel-title">{{ novel.title }}</span>
                  <span class="novel-author">{{ novel.author }}</span>
                </div>
                <div class="novel-rating">
                  <el-rate
                    :model-value="novel.rating / 2"
                    disabled
                    show-score
                    :score-template="`${novel.rating}`"
                    size="small"
                  />
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部：主题对比表格 -->
    <el-card shadow="never" class="comparison-card">
      <template #header>
        <div class="card-header">
          <span class="card-header-title">主题数据概览</span>
        </div>
      </template>
      <el-table :data="topicList" stripe style="width: 100%">
        <el-table-column prop="name" label="主题名称" width="140">
          <template #default="{ row }">
            <span class="topic-name-cell" @click="selectTopic(row)">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="novelCount" label="小说数量" align="center" sortable />
        <el-table-column prop="totalWords" label="总字数(亿)" align="center" sortable />
        <el-table-column prop="avgRating" label="平均评分" align="center" sortable>
          <template #default="{ row }">
            <span :style="{ color: row.avgRating >= 8 ? '#67c23a' : row.avgRating >= 7 ? '#e6a23c' : '#f56c6c' }">
              {{ row.avgRating }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="readerPercent" label="读者占比(%)" align="center" sortable />
        <el-table-column prop="trend" label="趋势" align="center" width="100">
          <template #default="{ row }">
            <el-tag :type="row.trend === '上升' ? 'success' : row.trend === '下降' ? 'danger' : 'info'" size="small">
              {{ row.trend }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

// ==================== Mock Data ====================
const topicList = ref([
  {
    name: '修仙飞升',
    novelCount: 3240,
    totalWords: 28.5,
    avgRating: 7.8,
    readerPercent: 22.3,
    trend: '上升',
    description: '以修炼体系为核心，主角从凡人逐步修炼成仙，经历各种磨难与机缘，最终飞升成仙的故事。涵盖筑基、金丹、元婴、化神等经典境界设定。',
    keywords: ['修仙', '境界', '飞升', '丹药', '法宝', '宗门'],
    x: 65, y: 75,
    topNovels: [
      { title: '凡人修仙传', author: '忘语', rating: 8.6 },
      { title: '一念永恒', author: '耳根', rating: 8.2 },
      { title: '仙逆', author: '耳根', rating: 8.8 }
    ]
  },
  {
    name: '都市异能',
    novelCount: 2180,
    totalWords: 19.2,
    avgRating: 7.5,
    readerPercent: 18.6,
    trend: '上升',
    description: '现代都市背景下，主角获得超自然能力后在都市中展开冒险。融合现代生活与超凡力量，展现普通人蜕变为强者的过程。',
    keywords: ['异能', '都市', '超能力', '觉醒', '进化', '变异'],
    x: 30, y: 55,
    topNovels: [
      { title: '全职法师', author: '乱', rating: 7.8 },
      { title: '我有一座恐怖屋', author: '我会修空调', rating: 8.4 },
      { title: '都市超级医圣', author: '断桥残雪', rating: 7.2 }
    ]
  },
  {
    name: '末日求生',
    novelCount: 1540,
    totalWords: 13.6,
    avgRating: 7.9,
    readerPercent: 12.1,
    trend: '上升',
    description: '描绘末日灾难来临后人类社会崩塌，主角在丧尸横行、资源匮乏的废土世界中求生、重建文明的故事。强调生存策略与人性考验。',
    keywords: ['末日', '丧尸', '废土', '求生', '避难所', '变异兽'],
    x: 80, y: 40,
    topNovels: [
      { title: '末日蟑螂', author: '偷偷写文', rating: 8.0 },
      { title: '黑暗血时代', author: '天下飘火', rating: 7.6 },
      { title: '末世超级系统', author: '流浪的军刀', rating: 7.4 }
    ]
  },
  {
    name: '宫廷权谋',
    novelCount: 1320,
    totalWords: 10.8,
    avgRating: 8.1,
    readerPercent: 10.5,
    trend: '稳定',
    description: '以古代宫廷为舞台，展现后宫嫔妃之间的明争暗斗，或朝堂之上各方势力的博弈角逐。智谋与情感交织。',
    keywords: ['宫斗', '权谋', '朝堂', '后宫', '皇权', '世家'],
    x: 45, y: 25,
    topNovels: [
      { title: '甄嬛传', author: '流潋紫', rating: 8.9 },
      { title: '庆余年', author: '猫腻', rating: 9.0 },
      { title: '琅琊榜', author: '海宴', rating: 9.2 }
    ]
  },
  {
    name: '星际科幻',
    novelCount: 1180,
    totalWords: 11.2,
    avgRating: 8.0,
    readerPercent: 9.8,
    trend: '上升',
    description: '以星际宇宙为背景，融合高科技、星际战争、外星文明等元素，展现人类在宇宙中的探索与征服。',
    keywords: ['星际', '机甲', '飞船', '外星', '联邦', '基因'],
    x: 20, y: 80,
    topNovels: [
      { title: '吞噬星空', author: '我吃西红柿', rating: 8.3 },
      { title: '星域四万年', author: '卧牛真人', rating: 7.9 },
      { title: '深空之流浪舰队', author: '最终永恒', rating: 7.7 }
    ]
  },
  {
    name: '校园青春',
    novelCount: 1050,
    totalWords: 6.8,
    avgRating: 7.3,
    readerPercent: 8.9,
    trend: '下降',
    description: '以校园为背景的青春故事，讲述青少年在学校中的成长、友情、爱情等经历。清新治愈风格为主。',
    keywords: ['校园', '青春', '暗恋', '学霸', '社团', '毕业'],
    x: 55, y: 50,
    topNovels: [
      { title: '你好，旧时光', author: '八月长安', rating: 8.1 },
      { title: '最好的我们', author: '八月长安', rating: 8.5 },
      { title: '致我们暖暖的小时光', author: '赵乾乾', rating: 7.6 }
    ]
  },
  {
    name: '商战风云',
    novelCount: 860,
    totalWords: 7.4,
    avgRating: 7.6,
    readerPercent: 6.2,
    trend: '稳定',
    description: '聚焦商业领域的明争暗斗，展现商界精英在资本市场中的较量。涉及创业、收购、金融博弈等商业主题。',
    keywords: ['商战', '创业', '金融', '收购', '资本', 'CEO'],
    x: 40, y: 65,
    topNovels: [
      { title: '大时代之金融之子', author: '范人忠', rating: 7.8 },
      { title: '重生之资本帝国', author: '零点浪漫', rating: 7.5 },
      { title: '超级电力强国', author: '给您添蘑菇啦', rating: 7.9 }
    ]
  }
])

// ==================== State ====================
const bubbleChartRef = ref(null)
let bubbleChart = null
const selectedTopic = ref(null)

// ==================== Methods ====================
function selectTopic(topic) {
  selectedTopic.value = topic
}

function initBubbleChart() {
  if (!bubbleChartRef.value) return
  bubbleChart = echarts.init(bubbleChartRef.value)

  const colorPalette = [
    '#409eff', '#67c23a', '#e6a23c', '#f56c6c',
    '#9b59b6', '#1abc9c', '#e67e22'
  ]

  const seriesData = topicList.value.map((topic, index) => ({
    name: topic.name,
    value: [topic.x, topic.y, topic.novelCount],
    symbolSize: Math.sqrt(topic.novelCount) * 1.5,
    itemStyle: {
      color: new echarts.graphic.RadialGradient(0.5, 0.5, 0.5, [
        { offset: 0, color: colorPalette[index] + 'cc' },
        { offset: 1, color: colorPalette[index] + '66' }
      ]),
      borderColor: colorPalette[index],
      borderWidth: 2
    },
    label: {
      show: true,
      formatter: '{b}',
      fontSize: 13,
      fontWeight: 'bold',
      color: '#303133'
    }
  }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const topic = topicList.value.find(t => t.name === params.name)
        if (!topic) return ''
        return `
          <div style="font-weight:bold;margin-bottom:4px;">${topic.name}</div>
          <div>小说数量: ${topic.novelCount} 部</div>
          <div>平均评分: ${topic.avgRating} 分</div>
          <div>读者占比: ${topic.readerPercent}%</div>
        `
      }
    },
    grid: {
      left: '8%',
      right: '8%',
      top: '8%',
      bottom: '8%'
    },
    xAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { show: false },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: {
        lineStyle: { type: 'dashed', color: '#e4e7ed' }
      }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { show: false },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: {
        lineStyle: { type: 'dashed', color: '#e4e7ed' }
      }
    },
    series: [{
      type: 'scatter',
      data: seriesData,
      emphasis: {
        scale: 1.2,
        itemStyle: {
          shadowBlur: 20,
          shadowColor: 'rgba(0, 0, 0, 0.3)'
        }
      },
      animationDuration: 1500,
      animationEasing: 'elasticOut'
    }]
  }

  bubbleChart.setOption(option)
  bubbleChart.on('click', (params) => {
    const topic = topicList.value.find(t => t.name === params.name)
    if (topic) {
      selectedTopic.value = topic
    }
  })
}

function handleResize() {
  bubbleChart && bubbleChart.resize()
}

// ==================== Lifecycle ====================
onMounted(() => {
  initBubbleChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (bubbleChart) {
    bubbleChart.dispose()
    bubbleChart = null
  }
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.page-container {
  padding: $spacing-lg;
  min-height: 100%;
}

.page-header {
  margin-bottom: $spacing-lg;

  .page-title {
    font-size: 22px;
    font-weight: 600;
    color: $text-primary;
    margin: 0 0 $spacing-xs 0;
  }

  .page-desc {
    font-size: 14px;
    color: $text-secondary;
    margin: 0;
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .card-header-title {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
  }

  .card-header-hint {
    font-size: 13px;
    color: $text-secondary;
  }
}

.chart-card {
  margin-bottom: $spacing-lg;

  :deep(.el-card__body) {
    padding: $spacing-md;
  }
}

.chart-container {
  width: 100%;
  height: 480px;
}

.detail-card {
  margin-bottom: $spacing-lg;

  :deep(.el-card__body) {
    padding: $spacing-md;
    max-height: 540px;
    overflow-y: auto;
  }
}

.empty-detail {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.topic-detail {
  .topic-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-md;

    .topic-name {
      font-size: 20px;
      font-weight: 600;
      color: $text-primary;
      margin: 0;
    }
  }

  .topic-stats {
    margin-bottom: $spacing-md;
  }

  .topic-desc {
    margin-bottom: $spacing-md;

    h4 {
      font-size: 14px;
      font-weight: 600;
      color: $text-primary;
      margin: 0 0 $spacing-xs 0;
    }

    p {
      font-size: 13px;
      color: $text-regular;
      line-height: 1.6;
      margin: 0;
    }
  }

  .topic-keywords {
    margin-bottom: $spacing-md;

    h4 {
      font-size: 14px;
      font-weight: 600;
      color: $text-primary;
      margin: 0 0 $spacing-sm 0;
    }

    .keyword-tag {
      margin-right: $spacing-xs;
      margin-bottom: $spacing-xs;
    }
  }

  .top-novels {
    h4 {
      font-size: 14px;
      font-weight: 600;
      color: $text-primary;
      margin: 0 0 $spacing-sm 0;
    }

    .novel-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: $spacing-sm $spacing-md;
      border-radius: $border-radius-sm;
      background: $bg-color;
      margin-bottom: $spacing-sm;

      .novel-info {
        display: flex;
        flex-direction: column;

        .novel-title {
          font-size: 14px;
          font-weight: 500;
          color: $text-primary;
        }

        .novel-author {
          font-size: 12px;
          color: $text-secondary;
          margin-top: 2px;
        }
      }

      .novel-rating {
        :deep(.el-rate) {
          height: 20px;
        }
      }
    }
  }
}

.comparison-card {
  margin-top: 0;

  .topic-name-cell {
    color: $primary-color;
    cursor: pointer;
    font-weight: 500;

    &:hover {
      text-decoration: underline;
    }
  }
}
</style>
