<template>
  <LoadingIcon :is-loading="true" />
</template>

<script>
export default {
  name: 'Auth',
  mounted () {
    this.authenticate()
  },
  methods: {
    authenticate () {
      this.$newhirepreboarding.authenticate(this.$route.query.token).then(() => {
        this.$router.push({ name: 'preboarding' })
      })
    }
  }
}
</script>
