<template>
  <div class="search-page">
    <div class="search-header">
      <h2>搜索结果：<span class="keyword">{{ keyword }}</span></h2>
      <p class="result-count">共找到 <strong>{{ totalResults }}</strong> 条相关结果</p>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="全部" name="all">
        <div class="result-list">
          <el-card v-for="item in allResults" :key="item.id" shadow="hover" class="result-item">
            <div class="result-content">
              <el-tag size="small" :type="item.tagType">{{ item.category }}</el-tag>
              <h3 class="result-title">{{ item.title }}</h3>
              <p class="result-desc">{{ item.desc }}</p>
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <el-tab-pane label="小说" name="novel">
        <div class="novel-list">
          <div v-for="item in novelResults" :key="item.id" class="novel-item">
            <div class="novel-cover" :style="{ background: item.gradient }"></div>
            <div class="novel-info">
              <h3>{{ item.title }}</h3>
              <p>作者：{{ item.author }}</p>
              <div class="novel-meta">
                <el-tag size="small">{{ item.type }}</el-tag>
                <el-rate :model-value="item.score" disabled show-score size="small" />
              </div>
              <p class="novel-desc">{{ item.desc }}</p>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="作者" name="author">
        <el-row :gutter="16">
          <el-col :span="8" v-for="item in authorResults" :key="item.id">
            <el-card shadow="hover" class="author-card">
              <div class="author-info">
                <el-avatar :size="48" :icon="UserFilled" />
                <div>
                  <h4>{{ item.name }}</h4>
                  <p>{{ item.novelCount }} 部作品</p>
                </div>
              </div>
              <div class="author-works">
                <el-tag v-for="w in item.works" :key="w" size="small" effect="plain">{{ w }}</el-tag>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="标签" name="tag">
        <div class="tag-cloud">
          <el-tag
            v-for="tag in tagResults"
            :key="tag.name"
            :style="{ fontSize: tag.size + 'px' }"
            class="tag-item"
            effect="plain"
          >
            {{ tag.name }} ({{ tag.count }})
          </el-tag>
        </div>
      </el-tab-pane>
    </el-tabs>

    <div class="pagination-wrapper">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="totalResults"
        :page-size="10"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { UserFilled } from '@element-plus/icons-vue'

const route = useRoute()
const keyword = computed(() => route.query.q || '')
const activeTab = ref('all')
const totalResults = ref(86)

const allResults = ref([
  { id: 1, category: '小说', tagType: '', title: '斗破苍穹', desc: '三十年河东，三十年河西，莫欺少年穷！天才少年萧炎在创造了家族空前绝后的修炼纪录后突然成了废人...' },
  { id: 2, category: '作者', tagType: 'success', title: '天蚕土豆', desc: '知名网络小说作家，代表作品《斗破苍穹》《武动乾坤》《大主宰》《元尊》...' },
  { id: 3, category: '小说', tagType: '', title: '完美世界', desc: '一粒尘可填海，一根草斩断日月星辰。荒域中走出一个少年，他注定要成为这个世界的主角...' },
  { id: 4, category: '标签', tagType: 'warning', title: '玄幻修仙', desc: '包含穿越、重生、升级、修仙等元素的小说集合，共收录 3,200 部作品...' },
  { id: 5, category: '小说', tagType: '', title: '遮天', desc: '九龙拉棺，一位大帝的陨落与重生。百年之后，一位少年从乱世中崛起...' }
])

const novelResults = ref([
  { id: 1, title: '斗破苍穹', author: '天蚕土豆', type: '玄幻', score: 4.5, gradient: 'linear-gradient(135deg, #667eea, #764ba2)', desc: '三十年河东，三十年河西，莫欺少年穷！' },
  { id: 2, title: '完美世界', author: '辰东', type: '玄幻', score: 4.3, gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)', desc: '一粒尘可填海，一根草斩断日月星辰。' },
  { id: 3, title: '遮天', author: '辰东', type: '仙侠', score: 4.6, gradient: 'linear-gradient(135deg, #fa709a, #fee140)', desc: '冰冷与黑暗并存的宇宙深处，九具庞大的龙尸拉着一口青铜棺。' },
  { id: 4, title: '诡秘之主', author: '爱潜水的乌贼', type: '悬疑', score: 4.8, gradient: 'linear-gradient(135deg, #434343, #000)', desc: '蒸汽与机械的浪潮中，谁能触及非凡？' }
])

const authorResults = ref([
  { id: 1, name: '天蚕土豆', novelCount: 6, works: ['斗破苍穹', '武动乾坤', '大主宰'] },
  { id: 2, name: '辰东', novelCount: 5, works: ['完美世界', '遮天', '神墓'] },
  { id: 3, name: '爱潜水的乌贼', novelCount: 4, works: ['诡秘之主', '一世之尊', '奥术神座'] }
])

const tagResults = ref([
  { name: '穿越', count: 1200, size: 22 }, { name: '重生', count: 1100, size: 20 },
  { name: '修仙', count: 950, size: 19 }, { name: '系统', count: 980, size: 19 },
  { name: '异能', count: 880, size: 17 }, { name: '热血', count: 650, size: 15 },
  { name: '冒险', count: 620, size: 15 }, { name: '末日', count: 550, size: 14 },
  { name: '宫斗', count: 500, size: 14 }, { name: '校园', count: 440, size: 13 },
  { name: '星际', count: 380, size: 13 }, { name: '甜宠', count: 360, size: 12 }
])
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.search-page {
  padding: $spacing-lg;
  min-height: 100%;
}

.search-header {
  margin-bottom: $spacing-lg;

  h2 {
    font-size: 20px;
    color: $text-primary;
    margin: 0 0 $spacing-xs 0;

    .keyword { color: $primary-color; }
  }

  .result-count {
    font-size: 13px;
    color: $text-secondary;
    margin: 0;
  }
}

.result-list {
  .result-item {
    margin-bottom: $spacing-md;
    cursor: pointer;
  }

  .result-title {
    font-size: 16px;
    color: $text-primary;
    margin: $spacing-sm 0 $spacing-xs;
  }

  .result-desc {
    font-size: 13px;
    color: $text-secondary;
    margin: 0;
    line-height: 1.6;
  }
}

.novel-list {
  .novel-item {
    display: flex;
    gap: $spacing-md;
    padding: $spacing-md;
    background: $bg-white;
    border-radius: $border-radius-md;
    box-shadow: $box-shadow-light;
    margin-bottom: $spacing-md;
    cursor: pointer;

    &:hover { box-shadow: $box-shadow; }
  }

  .novel-cover {
    width: 100px;
    height: 140px;
    border-radius: $border-radius-sm;
    flex-shrink: 0;
  }

  .novel-info {
    flex: 1;

    h3 { margin: 0 0 $spacing-xs; font-size: 16px; color: $text-primary; }
    p { margin: 0 0 $spacing-xs; font-size: 13px; color: $text-secondary; }
  }

  .novel-meta {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    margin-bottom: $spacing-xs;
  }

  .novel-desc {
    line-height: 1.6;
  }
}

.author-card {
  margin-bottom: $spacing-md;

  .author-info {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    margin-bottom: $spacing-md;

    h4 { margin: 0; font-size: 15px; }
    p { margin: 4px 0 0; font-size: 13px; color: $text-secondary; }
  }

  .author-works {
    display: flex;
    gap: $spacing-xs;
    flex-wrap: wrap;
  }
}

.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-md;
  padding: $spacing-lg;

  .tag-item {
    cursor: pointer;
    transition: all 0.3s;

    &:hover { transform: scale(1.1); }
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: $spacing-lg 0;
}
</style>
