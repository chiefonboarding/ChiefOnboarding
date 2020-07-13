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

      <v-card class="pa-2">
        <v-btn @click="$emit('add', 0)" block depressed class="my-1 mb-2">
          Add page
        </v-btn>
        <v-btn @click="$emit('add', 1)" block depressed class="my-1">
          Add folder
        </v-btn>
        <v-btn @click="$emit('add', 2)" block depressed>
          Add questions
        </v-btn>
        <v-divider />
        <v-btn @click="$emit('moveUp')" block depressed class="my-1 mt-2">
          move up
        </v-btn>
        <v-btn @click="$emit('moveDown')" block depressed class="my-1 mb-2">
          move down
        </v-btn>
        <v-divider />
        <v-btn @click="$emit('removeItem')" block depressed color="red" class="remove mt-2">
          remove
        </v-btn>
      </v-card>
    </v-menu>
  </div>
</template>

<script>
export default {
  name: 'ResourceOptions',
  props: {
    disableEmoji: {
      default: false,
      type: Boolean
    },
    removable: {
      default: false,
      type: Boolean
    }
  },
  data: () => ({
    menu: false
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
}
</style>
