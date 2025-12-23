import { LazyModalConfirmModal } from '#components'

interface ConfirmOptions {
  title?: string
  description?: string
  confirmLabel?: string
  cancelLabel?: string
  confirmColor?: 'primary' | 'error' | 'warning' | 'success' | 'info' | 'neutral'
  icon?: string
}

export function useConfirm() {
  const overlay = useOverlay()

  async function confirm(options: ConfirmOptions = {}): Promise<boolean> {
    const modal = overlay.create(LazyModalConfirmModal)

    const instance = modal.open({
      title: options.title,
      description: options.description,
      confirmLabel: options.confirmLabel,
      cancelLabel: options.cancelLabel,
      confirmColor: options.confirmColor,
      icon: options.icon
    })

    const result = await instance.result
    return result === true
  }

  return { confirm }
}
