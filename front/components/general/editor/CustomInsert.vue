<template>
  <div class="text-center">
    <v-menu
      v-model="menu"
      :close-on-content-click="false"
      :nudge-width="200"
      offset-x
    >
      <template v-slot:activator="{ on }">
        <font-awesome-icon v-on="on" :icon="['fas', 'plus-circle']" style="cursor: pointer; color: #f7ce85" />
      </template>

      <v-card style="max-width: 250px">
        <v-tabs v-model="tab" v-if="!disablePersonalize || !disableEmoji">
          <v-tab v-for="item in items" :key="item.tab">
            {{ item.tab }}
          </v-tab>
        </v-tabs>
        <v-tabs-items v-model="tab" v-if="!disablePersonalize || !disableEmoji">
          <v-tab-item key="Emoji" v-if="!disableEmoji" class="emoji-card">
            <button v-for="item in emoji" @click="addSVG(item)">
              {{ item }}
            </button>
          </v-tab-item>
          <v-tab-item key="Personalize">
            <v-list>
              <v-list-item @click="addPersonalize('{{first_name}}')">
                <v-list-item-title>{{ $t('textArea.firstName') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="addPersonalize('{{last_name}}')">
                <v-list-item-title>{{ $t('textArea.lastName') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="addPersonalize('{{email}}')">
                <v-list-item-title>{{ $t('textArea.email') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="addPersonalize('{{position}}')">
                <v-list-item-title>{{ $t('textArea.job') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="addPersonalize('{{manager}}')">
                <v-list-item-title>{{ $t('textArea.manager') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="addPersonalize('{{buddy}}')">
                <v-list-item-title>{{ $t('textArea.buddy') }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-tab-item>
        </v-tabs-items>
        <v-btn
          v-if="addOne"
          @click="$emit('addItem')"
          block
          class="mb-2"
          depressed
          color="primary"
        >
          Add list item
        </v-btn>
        <v-btn v-if="removable" @click="$emit('removeBlock')" block color="red" class="remove">
          remove
        </v-btn>
      </v-card>
    </v-menu>
  </div>
</template>

<script>
export default {
  name: 'CustomInsert',
  props: {
    disableEmoji: {
      default: false,
      type: Boolean
    },
    disablePersonalize: {
      default: false,
      type: Boolean
    },
    removable: {
      default: false,
      type: Boolean
    },
    addOne: {
      default: false,
      type: Boolean
    }
  },
  data: () => ({
    menu: false,
    tab: undefined,
    items: [
      { tab: 'Emoji' },
      { tab: 'Personalize' }
    ],
    emoji: [
      '🧡', '💛', '💚', '💙', '💜', '🖤', '💔', '💕', '💞', '💓', '💗', '💖', '💘', '😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇', '🙂', '🙃', '😉', '😌', '😍', '😘', '🥰', '😗', '😙', '😚', '😋', '😛', '😝', '😜', '🤪', '🤨', '🧐', '🤓', '😎', '🤩', '🥳', '😏', '😒', '😞', '😔', '😟', '😕', '🙁', '😣', '😖', '😫', '😩', '😢', '😭', '😤', '😠', '😡', '🤬', '🤯', '😳', '😱', '😨', '😰', '🥵', '🥺', '😥', '😓', '🤗', '🤔', '🤭', '🤫', '🤥', '😶', '😐', '😑', '😬', '🙄', '😯', '😦', '😧', '😮', '😲', '😴', '🤤', '😪', '😵', '🤐', '🥴', '🤮', '🤧', '😷', '🤒', '🤕', '🤑', '🤠', '😈', '👿', '👹', '👺', '🤡', '💩', '👻', '💀', '👽', '👾', '🤖', '🎃', '😺', '😸', '😹', '😻', '😼', '😽', '🙀', '😿', '😾', '🤲', '👐', '🙌', '👏', '🤝', '👍', '👎', '👊', '✊', '🤛', '🤜', '🤞', '✌', '🤟', '🤘', '👌', '👈', '👉', '👆', '👇', '☝', '✋', '🤚', '🖐', '🖖', '👋', '🤙', '💪', '🦵', '🦶', '🖕', '✍', '🙏', '💍', '💄', '💋', '👄', '👅', '👂', '👃', '👣', '👀', '🧠', '🦴', '👶', '👧', '🧒', '👦', '👩', '🧑', '👨', '👱', '🧔', '👵', '🧓', '👴', '👲', '👳', '🧕', '👮', '👷', '💂', '🕵', '👰', '🤵', '👸', '🤴', '🤶', '🎅', '🦸', '🦹', '🧙', '🧝', '🧛', '🧟', '🧞', '🧜', '🧚', '👼', '🤰', '🤱', '🙇', '💁', '🙅', '🙆', '🙋', '🤦', '🤷', '🙎', '🙍', '💇', '💆', '🧖', '💅', '🤳', '💃', '🕺', '👯', '🕴', '🚶', '🏃', '👫', '👭', '👬', '💑', '💏', '👪', '🧥', '👚', '👕', '👖', '🚗', '🚕', '🚙', '🚌', '🚎', '🏎', '🚓', '🚑', '🚒', '🚐', '🚚', '🚛', '🚜', '🛴', '🚲', '🛵', '🏍', '🚨', '🚔', '🚍', '🚘', '🚖', '🚡', '🚠', '🚟', '🚃', '🚋', '🚞', '🚝', '🚄', '🚅', '🚈', '🚂', '🚆', '🚇', '🚊', '🚉', '🛫', '🛬', '🛩', '💺', '🧳', '🛰', '🚀', '🛸', '🚁', '🛶', '⛵ ', '🚤', '🛥', '🛳', '⛴ ', '🚢', '⛽ ', '🚧', '🚦', '🚥', '🚏', '🗺', '🗿', '🗽', '🗼', '🏰', '🏯', '🏟', '🎡', '🎢', '🎠', '⛲', '⛱', '🏖', '🏝', '🏜', '🌋', '⛰', '🏔', '🗻', '🏕', '⛺', '🏠', '🏡', '🏘', '🏚', '🏗', '🏭', '🏢', '🏬', '🏣', '🏤', '🏥', '🏦', '🏨'
    ]
  }),
  mounted () {
    if (this.disableEmoji) {
      this.items = [
        { tab: 'Personalize' }
      ]
    }
  },
  methods: {
    addSVG (item) {
      this.$emit('clickedEmoji', item)
    },
    addPersonalize (item) {
      this.$emit('clickedPersonalize', item)
    }
  }
}
</script>

<style scoped>
.emoji-card {
  overflow-y: scroll;
  height: 200px;
  width: 100%;
  padding: 4px;
}
button {
  padding-right: 4px;
}
.remove {
  color: white;
  margin-top: 10px;
}
</style>
