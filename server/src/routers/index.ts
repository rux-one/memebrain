import { router } from '../trpc';
import { memeRouter } from './meme';

export const appRouter = router({
  meme: memeRouter,
});

export type AppRouter = typeof appRouter;
