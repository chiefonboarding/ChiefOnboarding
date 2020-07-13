<template>
  <div>
    <v-form>
      <v-col>
        <p class="ma-0">
          {{ $t('admin.fillInEmail') }}
        </p>
      </v-col>
      <v-col class="py-0">
        <v-text-field v-model="email" :label="$t('forms.email')" :color="$store.state.org.base_color" name="Email" type="email" />
      </v-col>
    </v-form>
    <v-col>
      <v-btn :loading="loading" :color="$store.state.org.base_color" @click="requestPass" type="submit" style="color: white; margin: 0px;">
        {{ $t('buttons.submit') }}
      </v-btn>
    </v-col>
  </div>
</template>

<script>
export default {
  data () {
    return {
      email: '',
      loading: false
    }
  },
  methods: {
    requestPass () {
      this.loading = true
      this.$user.requestPass({ email: this.email }).then((data) => {
        this.$router.push({ name: 'index' })
        this.$store.dispatch('showSnackbar', this.$t('admin.ifWeFind'))
      }).catch((error) => {
        error = error.response.data
        if ('email' in error) {
          this.$store.dispatch('showSnackbar', error.email[0])
        } else {
          this.$store.dispatch('showSnackbar', this.$t('admin.weCouldNotProcess'))
        }
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>
