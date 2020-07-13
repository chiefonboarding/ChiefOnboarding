<template>
  <div>
    <div v-for="(i, index) in value" :key="'q' + index">
      <v-text-field
        v-model="i.content"
        :label="$t('resource.question')"
        @click:append="value.splice(index, 1)"
        filled
        hide-details
        append-icon="close"
      />
      <div v-for="(j, index_) in i.items" :key="'o' + index_">
        <v-text-field
          v-model="j.text"
          :label="$t('resource.option')"
          @click:append="i.items.splice(index_, 1)"
          @click:prepend="setAnswer(i.items, index_, index)"
          :prepend-icon="(j.id === i.answer) ? 'radio_button_checked' : 'radio_button_unchecked'"
          filled
          hide-details
          append-icon="close"
        />
      </div>
      <v-btn @click="addItem(i.items)" depressed style="margin-left: 32px;margin-top: 4px;margin-bottom: 10px;">
        {{ $t('buttons.add') }}
      </v-btn>
    </div>
    <v-btn @click="addQuestion" color="primary">
      {{ $t('resource.addQuestion') }}
    </v-btn>
  </div>
</template>

<script>
export default {
  name: 'ResourceQuestions',
  props: {
    value: {
      type: Array,
      default: () => { return [] }
    }
  },
  methods: {
    addQuestion () {
      const uniqueId = this.getRandomString()
      this.value.push({
        'content': this.$t('resource.whatsThe'),
        'items': [{ 'id': uniqueId, 'text': '' }],
        'type': 'question',
        'answer': uniqueId
      })
    },
    addItem (items) {
      items.push({ 'text': '', 'id': this.getRandomString() })
    },
    setAnswer (items, itemIndex, index) {
      this.value[index].answer = items[itemIndex].id
    },
    getRandomString () {
      // from https://stackoverflow.com/a/6860916
      return (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1)
    }
  }
}
</script>
