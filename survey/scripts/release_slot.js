/**
 * Release abandoned task slots
 *
 * Usage:
 *   # Release specific task slot
 *   node scripts/release_slot.js /path/to/serviceAccount.json --task 2 --slot 1
 *
 *   # Release all in_progress slots for a task
 *   node scripts/release_slot.js /path/to/serviceAccount.json --task 2 --all
 *
 *   # Release all timed-out slots (older than 2 hours)
 *   node scripts/release_slot.js /path/to/serviceAccount.json --cleanup
 *
 *   # List all slot statuses
 *   node scripts/release_slot.js /path/to/serviceAccount.json --list
 */

const admin = require('firebase-admin');

// Parse arguments
const args = process.argv.slice(2);
const serviceAccountPath = args[0];

if (!serviceAccountPath || serviceAccountPath.startsWith('--')) {
  console.log('Usage: node release_slot.js <serviceAccount.json> [options]');
  console.log('');
  console.log('Options:');
  console.log('  --list              List all slot statuses');
  console.log('  --task N            Specify task ID');
  console.log('  --slot N            Specify slot number (1-3)');
  console.log('  --all               Release all in_progress slots for task');
  console.log('  --cleanup           Release all timed-out slots (>2 hours)');
  process.exit(1);
}

const serviceAccount = require(serviceAccountPath);
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  projectId: serviceAccount.project_id || 'acrb-e8cb4'
});

const db = admin.firestore();
const SLOT_TIMEOUT_MS = 2 * 60 * 60 * 1000; // 2 hours

function getArg(name) {
  const idx = args.indexOf(name);
  if (idx === -1) return null;
  if (name === '--list' || name === '--all' || name === '--cleanup') return true;
  return args[idx + 1];
}

async function listSlots() {
  console.log('\n=== Task Slot Status ===\n');

  const snapshot = await db.collection('amt_task_slots').get();
  const docs = snapshot.docs.sort((a, b) => {
    const aData = a.data();
    const bData = b.data();
    if (aData.taskId !== bData.taskId) return aData.taskId - bData.taskId;
    return aData.slotNum - bData.slotNum;
  });
  const now = Date.now();

  let currentTask = 0;
  docs.forEach(doc => {
    const data = doc.data();
    if (data.taskId !== currentTask) {
      if (currentTask !== 0) console.log('');
      currentTask = data.taskId;
      console.log(`Task ${data.taskId}:`);
    }

    let statusIcon = '🟢';
    let extra = '';

    if (data.status === 'completed') {
      statusIcon = '✅';
    } else if (data.status === 'in_progress') {
      statusIcon = '⏳';
      if (data.claimedAt) {
        const claimedTime = data.claimedAt.toMillis ? data.claimedAt.toMillis() : new Date(data.claimedAt).getTime();
        const elapsed = now - claimedTime;
        const hours = Math.floor(elapsed / (1000 * 60 * 60));
        const mins = Math.floor((elapsed % (1000 * 60 * 60)) / (1000 * 60));
        extra = ` (${hours}h ${mins}m ago)`;
        if (elapsed > SLOT_TIMEOUT_MS) {
          statusIcon = '⚠️ ';
          extra += ' [TIMED OUT]';
        }
      }
    }

    const claimedBy = data.claimedBy ? data.claimedBy.slice(0, 20) : '-';
    console.log(`  ${statusIcon} Slot ${data.slotNum}: ${data.status.padEnd(11)} | ${claimedBy}${extra}`);
  });

  console.log('\n');
}

async function releaseSlot(taskId, slotNum) {
  const docId = `task_${taskId}_slot_${slotNum}`;
  const docRef = db.collection('amt_task_slots').doc(docId);
  const doc = await docRef.get();

  if (!doc.exists) {
    console.log(`❌ Slot ${docId} not found`);
    return false;
  }

  const data = doc.data();
  if (data.status === 'completed') {
    console.log(`⚠️  Slot ${docId} is already completed, skipping`);
    return false;
  }

  if (data.status === 'available') {
    console.log(`ℹ️  Slot ${docId} is already available`);
    return false;
  }

  await docRef.update({
    claimedBy: null,
    claimedAt: null,
    status: 'available'
  });

  console.log(`✅ Released slot ${docId} (was claimed by ${data.claimedBy})`);
  return true;
}

async function releaseTaskSlots(taskId) {
  console.log(`\nReleasing all in_progress slots for Task ${taskId}...\n`);

  let released = 0;
  for (let slotNum = 1; slotNum <= 3; slotNum++) {
    const docId = `task_${taskId}_slot_${slotNum}`;
    const doc = await db.collection('amt_task_slots').doc(docId).get();

    if (doc.exists && doc.data().status === 'in_progress') {
      await releaseSlot(taskId, slotNum);
      released++;
    }
  }

  console.log(`\nReleased ${released} slot(s)`);
}

async function cleanupTimedOut() {
  console.log('\nCleaning up timed-out slots...\n');

  const now = Date.now();
  const snapshot = await db.collection('amt_task_slots')
    .where('status', '==', 'in_progress')
    .get();

  let released = 0;
  for (const doc of snapshot.docs) {
    const data = doc.data();
    if (data.claimedAt) {
      const claimedTime = data.claimedAt.toMillis ? data.claimedAt.toMillis() : new Date(data.claimedAt).getTime();
      if (now - claimedTime > SLOT_TIMEOUT_MS) {
        await doc.ref.update({
          claimedBy: null,
          claimedAt: null,
          status: 'available'
        });
        console.log(`✅ Released ${doc.id} (timed out, was ${data.claimedBy})`);
        released++;
      }
    }
  }

  console.log(`\nReleased ${released} timed-out slot(s)`);
}

async function main() {
  try {
    if (getArg('--list')) {
      await listSlots();
    } else if (getArg('--cleanup')) {
      await cleanupTimedOut();
    } else if (getArg('--task')) {
      const taskId = parseInt(getArg('--task'));

      if (getArg('--all')) {
        await releaseTaskSlots(taskId);
      } else if (getArg('--slot')) {
        const slotNum = parseInt(getArg('--slot'));
        await releaseSlot(taskId, slotNum);
      } else {
        console.log('Please specify --slot N or --all');
      }
    } else {
      await listSlots();
    }
  } catch (error) {
    console.error('❌ Error:', error.message);
  }

  process.exit(0);
}

main();
