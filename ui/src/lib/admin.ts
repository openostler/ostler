/** /admin serves the same app; the path reveals the admin screens (the server gates it). */
export const isAdminPath = (path: string): boolean => /^\/admin\/?$/.test(path);
