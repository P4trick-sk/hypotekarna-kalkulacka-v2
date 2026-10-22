/** Jediná chybová hláška (F2), oznámená čítačkám obrazovky. Kontajner je vždy v DOM, aby sa zmena prečítala. */
export function ErrorBanner({ message }: { message: string | null }) {
  return (
    <div role="alert" className={message ? 'error-banner' : 'error-banner empty'}>
      {message}
    </div>
  )
}
