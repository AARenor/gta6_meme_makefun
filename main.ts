// gta6-meme-x-01 entry. Node 22, standard library only.
//
// The entry is the X post itself: the meme picture and the post's text. This program has one job, and it is the
// only job the grader asks of it: hand the post's address over by copying POST.json out of the repository root
// and into the output directory the house reads. Nothing it writes about the post is judged.
//
// Run it the way the grader does, from the repository root:
//   mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts
// It prints nothing when the copy lands.

import { copyFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const POST_FILE = 'POST.json';

function paths(): { source: string; target: string; outputDir: string } {
  const repoDir = process.env.MAKEFUN_BOT_DIR ?? '/bot';
  const outputDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
  return {
    source: join(repoDir, POST_FILE),
    target: join(outputDir, POST_FILE),
    outputDir,
  };
}

function deliver(source: string, target: string, outputDir: string): void {
  mkdirSync(outputDir, { recursive: true });
  try {
    copyFileSync(source, target);
  } catch (error) {
    console.error(`main.ts: could not copy ${source} to ${target}: ${(error as Error).message}`);
    process.exit(1);
  }
}

const { source, target, outputDir } = paths();
deliver(source, target, outputDir);
