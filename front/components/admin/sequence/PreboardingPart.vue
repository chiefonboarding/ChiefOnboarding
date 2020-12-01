<template>
  <v-timeline-item
    color="dark"
    icon="fas fa-star"
  >
    <v-card
      color="dark"
      dark
    >
      <v-card-title class="title" style="padding-bottom: 5px; padding-top: 5px;">
        <v-row>
          <v-col>Pre-boarding</v-col>
          <v-col>
            <v-btn
              @click="$emit('openPreview')"
              color="secondary"
              small
              class="ma-0"
              style="float:right"
            >
              {{ $t('newhires.preview') }}
            </v-btn>
            <v-btn
              v-if="onNewHirePage"
              @click="$emit('openAccessModal')"
              color="secondary"
              small
              class="ma-0"
              style="float:right; margin-right: 11px !important;"
            >
              {{ $t('newhires.giveAccess') }}
            </v-btn>
            <v-btn
              @click="showPreboardingItemsModal=true"
              color="primary"
              small
              class="ma-0"
              style="float:right; margin-right: 11px !important;"
            >
              {{ $t('buttons.add') }}
            </v-btn>
          </v-col>
        </v-row>
      </v-card-title>
      <v-card-text class="white text--primary pt-3">
        <draggable v-model="value" @change="updateOrder" :disabled="!this.onNewHirePage">
          <v-row
            v-for="(i, index) in value"
            :key="index"
            style="cursor: pointer"
            @click="editItem(i)"
          >
            <v-col sm="11" class="py-0">
              <i class="fas fa-align-left mr-3" />{{ i.name }}
            </v-col>
            <v-col @click.stop="removeItem(i.id)" sm="1" class="red-remove py-0">
              <i class="far fa-times-circle pointer" />
            </v-col>
          </v-row>
        </draggable>
        <p v-if="value.length === 0">
          {{ $t('newhires.noItemsYet') }}
        </p>
      </v-card-text>
    </v-card>
    <PreboardingModal v-model="showPreboardingModal" :preboarding="item" @change="changedItem" />
    <SelectTemplates v-model="showPreboardingItemsModal" :items="$store.state.preboarding.all" @clickedItem="addItem" />
  </v-timeline-item>
</template>

<script>
import draggable from 'vuedraggable'
import PreboardingModal from '@/components/admin/collection/PreboardingModal'

export default {
  name: 'PreboardingPart',
  components: { draggable, PreboardingModal },
  props: {
    value: {
      required: true,
      type: Array
    },
    onNewHirePage: {
      default: false,
      type: Boolean
    }
  },
  data: () => ({
    showPreboardingModal: false,
    showPreboardingItemsModal: false,
    item: {}
  }),
  methods: {
    addItem (preboardingItem) {
      if (!this.onNewHirePage) {
        this.value.push(preboardingItem)
        return
      }
      this.$newhires.addTask(this.$route.params.id, { type: 'preboarding', item: preboardingItem }).then((data) => {
        this.value.push(data)
      })
    },
    updateOrder (value) {
      if (this.onNewHirePage) {
        this.value.forEach((one, index) => {
          one.order = index
        })
        this.$newhires.changePreboardingOrder(this.$route.params.id, this.value)
      } else {
        this.$emit('input', this.value)
      }
    },
    changedItem (value) {
      this.removeItem(value.remove)
      this.addItem(value.add)
    },
    editItem (value) {
      this.item = value
      this.showPreboardingModal = true
    },
    removeItem (item) {
      if (!this.onNewHirePage) {
        const index = this.value.findIndex(a => a.id === item)
        this.value.splice(index, 1)
        return
      }
      this.$newhires.deleteTask(this.$route.params.id, { type: 'preboarding', item: { id: item } }).then((data) => {
        const index = this.value.findIndex(a => a.id === item)
        this.value.splice(index, 1)
      }).catch(() => {
        this.$store.dispatch('showSnackbar', this.$t('newhires.notRemoved'))
      })
    }
  }
}
</script>
