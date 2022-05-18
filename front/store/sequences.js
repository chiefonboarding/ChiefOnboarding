import _ from 'lodash'

export const state = () => ({
  all: [],
  sequence: {},
  collection: {},
  hasPreboarding: false,
  hasAutoAdd: false,
  item: {
    'preboarding': [],
    'to_do': [],
    'resources': [],
    'name': ''
  }
})

export const mutations = {
  setAllSequences (state, all) {
    state.all = all
  },
  setSequenceFull (state, seq) {
    state.item = seq
  },
  hasPreboarding (state) {
    state.hasPreboarding = !state.hasPreboarding
  },
  resetPreboarding (state) {
    state.hasPreboarding = false
  },
  setAutoAdd (state) {
    state.hasAutoAdd = !state.hasAutoAdd
  },
  resetAutoAdd (state) {
    state.hasAutoAdd = false
  },
  setCollection (state, col) {
    state.collection = col
  },
  setSequenceName (state, col) {
    state.item.name = col
  },
  setSequence (state, seq) {
    let items = []
    items = items.concat(_.sortBy(seq.filter(a => a.condition_type === 2), [a => a.days])).reverse()
    items = items.concat(_.sortBy(seq.filter(a => a.condition_type === 0), [a => a.days]))
    items = items.concat(seq.filter(a => a.condition_type === 1))
    state.sequence = items
  },
  resetItem (state) {
    state.item = {
      'preboarding': [],
      'to_do': [],
      'resources': [],
      'name': ''
    }
  },
  removeItem (state, item) {
    let type = item.type
    if (item.type == "slack_messages" || item.type == "text_messages" || item.type == "emails") {
      type = "external_messages"
    }
    state.sequence[item.block][type] = state.sequence[item.block][type].filter(a => a.id !== item.id)
  },
  addItem (state, item) {
    state.sequence[item.block][item.type].push(item.item)
  },
  removeTimeLineItem (state, index) {
    state.sequence.splice(index.index, 1)
  },
  addTimeLineItem (state, item) {
    state.sequence.push(item)
    let items = []
    items = items.concat(_.sortBy(state.sequence.filter(a => a.condition_type === 2), [a => a.days])).reverse()
    items = items.concat(_.sortBy(state.sequence.filter(a => a.condition_type === 0), [a => a.days]))
    items = items.concat(state.sequence.filter(a => a.condition_type === 1))
    state.sequence = items
  },
  changeCondition (state, item) {
    const temp = []
    item.conditions.forEach((one) => {
      temp.push(one)
    })
    state.sequence[item.index].condition_to_do = temp
  },
  changeConditionDay (state, item) {
    state.sequence[item.index].days = parseInt(item.day)
    let items = []
    items = items.concat(_.sortBy(state.sequence.filter(a => a.condition_type === 2), [a => a.days])).reverse()
    items = items.concat(_.sortBy(state.sequence.filter(a => a.condition_type === 0), [a => a.days]))
    items = items.concat(state.sequence.filter(a => a.condition_type === 1))
    state.sequence = items
  },
  changeTextModal (state, bool) {
    state.showTextModal = bool
  },
  changeEmailModal (state, bool) {
    state.showEmailModal = bool
  },
  changeTaskModal (state, bool) {
    state.showTaskModal = bool
  }
}
