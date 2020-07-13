import Vue from 'vue'
import moment from 'moment'
import LoadingIcon from '~/components/general/LoadingIcon.vue'
import VFile from '~/components/general/VFile.vue'
import TemplateComp from '~/components/general/TemplateComp.vue'
import TemplateCompInner from '~/components/general/TemplateCompInner.vue'
import TagsSelector from '~/components/general/TagsSelector.vue'
import VTextFieldEmoji from '~/components/general/VTextFieldEmoji.vue'
import CustomForm from '~/components/general/CustomForm.vue'
import Editor from '~/components/general/editor/Editor.vue'
import VTextAreaEmoji from '@/components/general/VTextAreaEmoji'
import SelectTemplates from '@/components/general/SelectTemplates'

Vue.component('LoadingIcon', LoadingIcon)
Vue.component('TemplateCompInner', TemplateCompInner)
Vue.component('TemplateComp', TemplateComp)
Vue.component('CustomForm', CustomForm)
Vue.component('Editor', Editor)
Vue.component('VTextFieldEmoji', VTextFieldEmoji)
Vue.component('TagsSelector', TagsSelector)
Vue.component('v-file', VFile)
Vue.component('VTextAreaEmoji', VTextAreaEmoji)
Vue.component('SelectTemplates', SelectTemplates)

// filters

Vue.filter('timeAgo', function (value) {
  if (value === null) {
    return 'No deadline'
  }
  return moment.utc(value).fromNow()
})

Vue.filter('timeAgoShort', function (value) {
  const ms = moment(value).diff(moment())
  if (ms > 259200000) { // 72 hours
    return moment.utc(value).format('ll')
  }
  if (ms < 0) {
    return 'overdue'
  }
  return moment.utc(value).fromNow()
})

Vue.filter('dateTimeFormat', function (value) {
  return moment.utc(value).format('ll')
})

Vue.filter('prio', function (value) {
  if (value === 1) {
    // return VueI18n.$t('hrTask.low')
    return 'low'
  } else if (value === 2) {
    // return VueI18n.$t('hrTask.medium')
    return 'medium'
  } else {
    return 'high'
    // return VueI18n.$t('hrTask.high')
  }
})
