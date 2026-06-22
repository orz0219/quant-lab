<template>
  <div>
    <div class="bg-aurora"></div>
    <div class="bg-grid"></div>
    <Nav active="forum" />
    <main class="workspace-single">
      <section class="headline center">
        <h1 class="head-title"><span class="grad-text">论坛</span> · 讨论分享</h1>
        <p class="head-sub">分享你的交易思路、策略经验，和其他交易者一起交流讨论。</p>
      </section>
      <section class="forum">
        <div class="forum-head">
          <div class="card-title"><span class="title-dot cyan"></span>策略讨论</div>
          <div class="forum-tabs">
            <span :class="['tab', { active: tab === 'latest' }]" @click="tab = 'latest'">最新</span>
            <span :class="['tab', { active: tab === 'hot' }]" @click="tab = 'hot'">热门</span>
            <span :class="['tab', { active: tab === 'elite' }]" @click="tab = 'elite'">精华</span>
          </div>
        </div>
        <div class="glass post-box">
          <div class="avatar">我</div>
          <div class="post-input">
            <input type="text" v-model="postForm.title" placeholder="标题" />
            <textarea v-model="postForm.content" rows="3" placeholder="说点什么..."></textarea>
            <div class="post-actions">
              <input type="text" v-model="postForm.tags" placeholder="标签（可选）" />
              <button class="btn-gradient" @click="submitPost">发布</button>
            </div>
          </div>
        </div>
        <div class="post-list">
          <article v-for="(post, i) in posts" :key="i" class="post glass">
            <div class="avatar">{{ post.author[0] }}</div>
            <div class="post-body">
              <div class="post-meta">
                <span class="author">{{ post.author }}</span>
                <span class="when">{{ post.when }}</span>
                <span v-for="tag in post.tags" :key="tag" class="tag">{{ tag }}</span>
              </div>
              <h3 class="post-title">{{ post.title }}</h3>
              <p class="post-content">{{ post.content }}</p>
              <div class="post-stats">
                <span>👍 {{ post.likes }}</span>
                <span>💬 {{ post.comments }}</span>
              </div>
            </div>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import Nav from '@/components/Nav.vue'

const tab = ref('latest')
const postForm = reactive({ title: '', content: '', tags: '' })
const posts = ref([
  { author: '李思齐', when: '2 小时前', tags: ['均线', '趋势'], title: 'MA5/MA20 金叉策略在 A 股的表现', content: '把 MA5 上穿 MA20 作为买入信号，在牛市里非常灵敏；但震荡市来回打脸，怎么办？', likes: 24, comments: 8 },
  { author: '王维', when: '昨天', tags: ['pinBar', '反转'], title: 'pinBar 在 2B 形态心得', content: '最近测试了 pinBar 反转策略，发现小市值股票的 pinBar 非常容易触发假突破。', likes: 18, comments: 5 },
  { author: '张泽', when: '3 天前', tags: ['动量', '短线'], title: '动量 + 趋势 + 均线过滤真的有用吗？', content: '我用过去 20 日涨幅作为动量因子，再叠加 MA20 作为趋势过滤，回测收益提升了约 10%。', likes: 32, comments: 14 },
])

function submitPost() {
  if (!postForm.title.trim()) return
  posts.value.unshift({ author: '我', when: '刚刚', tags: postForm.tags.split(',').filter(Boolean).map(t => t.trim()), title: postForm.title, content: postForm.content, likes: 0, comments: 0 })
  postForm.title = ''; postForm.content = ''; postForm.tags = ''
}
</script>
