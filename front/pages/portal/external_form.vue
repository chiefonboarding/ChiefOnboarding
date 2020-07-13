<template>
  <v-container>
    <LoadingIcon :is-loading="loading" />
    <v-row v-if="!allowed" wrap row>
      <v-col sm="6" offset-sm="3">
        <v-card class="pa-3">
          <p>{{ $t('newHirePortal.pageDoesNotExist') }}</p>
        </v-card>
      </v-col>
    </v-row>
    <v-row v-if="!loading" wrap row>
      <v-col sm="6" offset-sm="3">
        <v-card v-if="!completed" class="pa-3">
          <CustomForm :id="$route.query.task_id" :data="formData" :org="$store.state.baseInfo" :external="true" @input="data = arguments[0]" />
          <v-btn :loading="submitting" :color="$store.state.baseInfo.color" @click="submitForm()" style="color: white">
            {{ $t('buttons.submit') }}
          </v-btn>
        </v-card>
        <v-card v-else-if="allowed" style="width:100%" class="pa-3">
          {{ $t('newHirePortal.thanks') }}
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import CustomForm from '@/components/preboarding/CustomForm'
export default {
  name: 'ExternalForm',
  layout: 'newhire',
  components: {
    CustomForm
  },
  data () {
    return {
      allowed: true,
      formData: [],
      data: [],
      loading: false,
      submitting: false,
      completed: false
    }
  },
  mounted () {
    this.$store.commit('hideNewHireMenu')
    if (!('code' in this.$route.query && 'task_id' in this.$route.query)) {
      this.allowed = false
      return
    }
    this.$newhirepart.getExternalForm({ 'code': this.$route.query.code, 'task_id': this.$route.query.task_id }).then((response) => {
      this.formData = response.data
    }).catch((response) => {
      if ('completed' in response) {
        this.completed = true
      } else {
        this.allowed = false
      }
    })
  },
  methods: {
    submitForm (i) {
      this.submitting = true
      this.$newhirepart.postExternalForm({ 'code': this.$route.query.code, 'task_id': this.$route.query.task_id, 'data': this.data }).then((response) => {
        this.completed = true
      }).catch((response) => {
        this.allowed = false
        this.$store.dispatch('showSnackbar', this.$t('newHirePortal.couldNotSend'))
      }).finally(() => {
        this.submitting = false
      })
    }
  }
}
</script>

<!-- Add 'scoped' attribute to limit CSS to this component only -->
<style scoped>
.mobile {
  display: none;
}
.sub{
  color: #8D8D8D;
  margin-top: 10px;
}
.inner {
  padding: 20px;
}
.item {
  width: 213px;
}
.tooltip.is-primary:after {
  background-color: white;
  color: #363636;
}
.tooltip.is-top.is-primary:before {
  border-top: 5px solid white;
}
.active {
  border-left: 3px solid green;
  padding-left: 17px !important;
}
.active.calendar {
  border-left: 3px solid blue;
}
.today {
  border-bottom: 4px solid green;
}
.overdue {
  border: 0;
  border-bottom: 3px solid indianred;
}
</style>
