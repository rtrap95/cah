export function usePagination<T>(items: Ref<T[]> | ComputedRef<T[]>, itemsPerPage = 30) {
  const currentPage = ref(1)

  const totalPages = computed(() => Math.ceil(items.value.length / itemsPerPage))

  const paginatedItems = computed(() => {
    const start = (currentPage.value - 1) * itemsPerPage
    const end = start + itemsPerPage
    return items.value.slice(start, end)
  })

  const hasNextPage = computed(() => currentPage.value < totalPages.value)
  const hasPrevPage = computed(() => currentPage.value > 1)

  function nextPage() {
    if (hasNextPage.value) {
      currentPage.value++
    }
  }

  function prevPage() {
    if (hasPrevPage.value) {
      currentPage.value--
    }
  }

  function goToPage(page: number) {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
    }
  }

  function reset() {
    currentPage.value = 1
  }

  // Reset to page 1 when items change significantly
  watch(() => items.value.length, (newLen, oldLen) => {
    if (newLen !== oldLen && currentPage.value > Math.ceil(newLen / itemsPerPage)) {
      currentPage.value = Math.max(1, Math.ceil(newLen / itemsPerPage))
    }
  })

  return {
    currentPage,
    totalPages,
    paginatedItems,
    hasNextPage,
    hasPrevPage,
    nextPage,
    prevPage,
    goToPage,
    reset
  }
}
