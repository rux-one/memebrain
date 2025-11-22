import { z } from 'zod';
import { router, publicProcedure } from '../trpc';

export const memeRouter = router({
  search: publicProcedure
    .input(z.object({ query: z.string().optional() }))
    .query(({ input }) => {
      return {
        message: 'Search is unimplemented in this iteration',
        results: [],
        query: input.query
      };
    }),
});
