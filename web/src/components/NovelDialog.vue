<template>
  <el-dialog
    v-model="show"
    :title="novel.title"
    width="720px"
    destroy-on-close
    class="novel-dialog"
  >
    <template #header>
      <div class="dialog-header">
        <span class="dialog-title">{{ novel.title }}</span>
        <el-tag size="small" effect="light">{{ novel.type }}</el-tag>
      </div>
    </template>

    <div class="novel-detail" style="position: relative;">
      <DanmakuLayer v-if="show" />

      <div class="detail-top">
        <div class="detail-cover" :style="{ background: coverGradient }"></div>
        <div class="detail-info">
          <p><strong>作者：</strong>{{ novel.author }}</p>
          <p><strong>类型：</strong>{{ novel.type }}</p>
          <p><strong>字数：</strong>{{ novel.wordCount }}</p>
          <p><strong>状态：</strong><el-tag size="small" :type="novel.status === '连载中' ? 'success' : 'info'">{{ novel.status }}</el-tag></p>
          <p><strong>评分：</strong><el-rate :model-value="novel.score" disabled show-score size="small" /></p>
          <p class="desc"><strong>简介：</strong>{{ novel.desc }}</p>
        </div>
      </div>

      <el-tabs v-model="activeTab" class="detail-tabs">
        <el-tab-pane label="最新章节" name="chapters">
          <div class="chapter-list">
            <div v-for="ch in chapters" :key="ch.id" class="chapter-item">
              <span class="ch-name">{{ ch.name }}</span>
              <span class="ch-date">{{ ch.date }}</span>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="读者评论" name="comments">
          <div class="comment-list">
            <div v-for="c in comments" :key="c.id" class="comment-item">
              <el-avatar :size="36" :icon="UserFilled" />
              <div class="comment-body">
                <div class="comment-header">
                  <span class="comment-user">{{ c.user }}</span>
                  <el-rate :model-value="c.rating" disabled size="small" />
                </div>
                <p class="comment-text">{{ c.text }}</p>
                <span class="comment-time">{{ c.time }}</span>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="相关推荐" name="related">
          <el-row :gutter="12">
            <el-col :span="6" v-for="r in relatedNovels" :key="r.id">
              <div class="related-card">
                <div class="related-cover" :style="{ background: r.gradient }"></div>
                <span class="related-name">{{ r.title }}</span>
                <span class="related-author">{{ r.author }}</span>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
    </div>

    <template #footer>
      <el-button @click="handleCollect" :type="collected ? 'warning' : 'default'">
        <el-icon><StarFilled v-if="collected" /><Star v-else /></el-icon>
        {{ collected ? '已收藏' : '收藏' }}
      </el-button>
      <el-button type="primary">开始阅读</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { UserFilled, Star, StarFilled } from '@element-plus/icons-vue'
import DanmakuLayer from './DanmakuLayer.vue'

const props = defineProps({
  visible: Boolean,
  novelId: [Number, String]
})

const emit = defineEmits(['update:visible', 'collect'])

const show = computed({
  get: () => props.visible,
  set: v => emit('update:visible', v)
})

const activeTab = ref('chapters')
const collected = ref(false)

const novel = ref({
  title: '斗破苍穹', author: '天蚕土豆', type: '玄幻', wordCount: '532万字',
  status: '已完结', score: 4.5,
  desc: '三十年河东，三十年河西，莫欺少年穷！天才少年萧炎在创造了家族空前绝后的修炼纪录后突然成了废人，种种打击接踵而至。'
})

const coverGradient = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'

const chapters = ref(Array.from({ length: 10 }, (_, i) => ({
  id: i, name: `第${2150 - i}章 ${['风云再起', '巅峰对决', '终极之战', '尘埃落定', '新的征程', '暗流涌动', '绝境求生', '王者归来', '天地变色', '破茧重生'][i]}`,
  date: `2025-03-${String(17 - i).padStart(2, '0')}`
})))

const comments = ref([
  { id: 1, user: '书虫小王', rating: 5, text: '经典之作，百看不厌！', time: '2小时前' },
  { id: 2, user: '夜读者', rating: 4, text: '剧情紧凑，人物刻画生动。', time: '5小时前' },
  { id: 3, user: '追更达人', rating: 5, text: '萧炎的成长线写得太好了。', time: '1天前' },
  { id: 4, user: '老书虫', rating: 4, text: '世界观宏大，战斗场面震撼。', time: '2天前' },
  { id: 5, user: '新人读者', rating: 3, text: '后期有些拖沓，但整体不错。', time: '3天前' }
])

const relatedNovels = ref([
  { id: 1, title: '武动乾坤', author: '天蚕土豆', gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)' },
  { id: 2, title: '大主宰', author: '天蚕土豆', gradient: 'linear-gradient(135deg, #fa709a, #fee140)' },
  { id: 3, title: '完美世界', author: '辰东', gradient: 'linear-gradient(135deg, #2196f3, #0d47a1)' },
  { id: 4, title: '遮天', author: '辰东', gradient: 'linear-gradient(135deg, #a18cd1, #fbc2eb)' }
])

function handleCollect() {
  collected.value = !collected.value
  emit('collect', { novelId: props.novelId, collected: collected.value })
}
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.dialog-header {
  display: flex;
  align-items: center;
  gap: $spacing-sm;

  .dialog-title {
    font-size: 18px;
    font-weight: 700;
  }
}

.detail-top {
  display: flex;
  gap: $spacing-lg;
  margin-bottom: $spacing-lg;
}

.detail-cover {
  width: 180px;
  height: 240px;
  border-radius: $border-radius-md;
  flex-shrink: 0;
}

.detail-info {
  flex: 1;

  p {
    margin: 0 0 $spacing-sm;
    font-size: 14px;
    color: $text-regular;
  }

  .desc {
    line-height: 1.7;
    color: $text-secondary;
  }
}

.chapter-list {
  .chapter-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid $border-light;
    cursor: pointer;

    &:hover { color: $primary-color; }

    .ch-date { font-size: 12px; color: $text-secondary; }
  }
}

.comment-list {
  .comment-item {
    display: flex;
    gap: $spacing-md;
    padding: $spacing-md 0;
    border-bottom: 1px solid $border-light;
  }

  .comment-body { flex: 1; }

  .comment-header {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    margin-bottom: $spacing-xs;
  }

  .comment-user { font-weight: 600; font-size: 14px; }
  .comment-text { margin: $spacing-xs 0; font-size: 14px; color: $text-regular; }
  .comment-time { font-size: 12px; color: $text-secondary; }
}

.related-card {
  text-align: center;
  cursor: pointer;

  .related-cover {
    width: 100%;
    height: 120px;
    border-radius: $border-radius-sm;
    margin-bottom: $spacing-xs;
  }

  .related-name {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: $text-primary;
  }

  .related-author {
    font-size: 12px;
    color: $text-secondary;
  }
}
</style>
