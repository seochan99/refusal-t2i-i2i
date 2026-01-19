/**
 * Initialize Task Slots for Race-Condition-Free Task Assignment
 *
 * Creates 30 slot documents (10 tasks × 3 slots) in the `amt_task_slots` collection.
 * Each slot can be atomically claimed by one user using Firestore transactions.
 *
 * Usage:
 *   cd survey && node scripts/init_task_slots.js
 *
 * Prerequisites:
 *   - Firebase Admin SDK configured (gcloud auth application-default login)
 *   - Or set GOOGLE_APPLICATION_CREDENTIALS environment variable
 */

const admin = require('firebase-admin');

// Firebase Admin SDK initialization
// Option 1: Use service account file (set GOOGLE_APPLICATION_CREDENTIALS env var)
// Option 2: Pass service account path as argument: node init_task_slots.js /path/to/serviceAccount.json
const serviceAccountPath = process.argv[2] || process.env.GOOGLE_APPLICATION_CREDENTIALS;

if (serviceAccountPath) {
  const serviceAccount = require(serviceAccountPath);
  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    projectId: serviceAccount.project_id || 'acrb-e8cb4'
  });
} else {
  // Fallback to Application Default Credentials
  admin.initializeApp({
    projectId: 'acrb-e8cb4'
  });
}

const db = admin.firestore();

const TOTAL_TASKS = 10;
const SLOTS_PER_TASK = 3;

async function initTaskSlots() {
  console.log('=== Initializing Task Slots ===\n');

  try {
    // Check if slots already exist
    const existingSlots = await db.collection('amt_task_slots').limit(1).get();

    if (!existingSlots.empty) {
      console.log('⚠️  amt_task_slots collection already has data.');
      console.log('   Use --force flag to reinitialize (WARNING: this will reset all slots)\n');

      // Show current state
      const allSlots = await db.collection('amt_task_slots').get();
      const stats = { available: 0, in_progress: 0, completed: 0 };
      allSlots.forEach(doc => {
        const data = doc.data();
        stats[data.status] = (stats[data.status] || 0) + 1;
      });
      console.log('Current slot status:');
      console.log(`  - Available: ${stats.available}`);
      console.log(`  - In Progress: ${stats.in_progress}`);
      console.log(`  - Completed: ${stats.completed}`);

      if (!process.argv.includes('--force')) {
        process.exit(0);
      }
      console.log('\n--force flag detected. Reinitializing all slots...\n');
    }

    // First, get existing completions from amt_task_completions
    console.log('📋 Checking existing task completions...');
    const completionsSnapshot = await db.collection('amt_task_completions').get();
    const completionsByTask = new Map(); // taskId -> [userId1, userId2, ...]

    completionsSnapshot.forEach(doc => {
      const data = doc.data();
      const taskId = data.taskId;
      const userId = data.userId;
      if (taskId && userId) {
        if (!completionsByTask.has(taskId)) {
          completionsByTask.set(taskId, []);
        }
        const users = completionsByTask.get(taskId);
        if (!users.includes(userId)) {
          users.push(userId);
        }
      }
    });

    console.log('Existing completions:');
    completionsByTask.forEach((users, taskId) => {
      console.log(`  Task ${taskId}: ${users.length} completions`);
    });
    console.log('');

    // Use batched writes for atomicity
    const batch = db.batch();
    let slotCount = 0;

    for (let taskId = 1; taskId <= TOTAL_TASKS; taskId++) {
      const completedUsers = completionsByTask.get(taskId) || [];

      for (let slotNum = 1; slotNum <= SLOTS_PER_TASK; slotNum++) {
        const docId = `task_${taskId}_slot_${slotNum}`;
        const docRef = db.collection('amt_task_slots').doc(docId);

        // Check if this slot should be marked as completed
        const slotIndex = slotNum - 1;
        const isCompleted = slotIndex < completedUsers.length;
        const claimedBy = isCompleted ? completedUsers[slotIndex] : null;

        batch.set(docRef, {
          taskId: taskId,
          slotNum: slotNum,
          claimedBy: claimedBy,
          claimedAt: isCompleted ? admin.firestore.FieldValue.serverTimestamp() : null,
          status: isCompleted ? 'completed' : 'available'
        });

        slotCount++;
      }
    }

    await batch.commit();
    console.log(`✅ Created ${slotCount} task slots (${TOTAL_TASKS} tasks × ${SLOTS_PER_TASK} slots)\n`);

    // Verify creation
    const verifySnapshot = await db.collection('amt_task_slots').get();
    const finalStats = { available: 0, in_progress: 0, completed: 0 };
    verifySnapshot.forEach(doc => {
      const data = doc.data();
      finalStats[data.status] = (finalStats[data.status] || 0) + 1;
    });

    console.log(`📊 Final slot status:`);
    console.log(`  - Available: ${finalStats.available}`);
    console.log(`  - In Progress: ${finalStats.in_progress}`);
    console.log(`  - Completed: ${finalStats.completed}\n`);

    // Print slot summary for first few tasks
    console.log('Slot Structure (first 3 tasks):');
    console.log('┌──────────┬────────┬───────────┬─────────────────────────┐');
    console.log('│ Task ID  │ Slot # │ Status    │ ClaimedBy               │');
    console.log('├──────────┼────────┼───────────┼─────────────────────────┤');

    for (let taskId = 1; taskId <= Math.min(3, TOTAL_TASKS); taskId++) {
      for (let slotNum = 1; slotNum <= SLOTS_PER_TASK; slotNum++) {
        const docId = `task_${taskId}_slot_${slotNum}`;
        const doc = await db.collection('amt_task_slots').doc(docId).get();
        const data = doc.data();
        const claimedBy = data.claimedBy ? data.claimedBy.slice(0, 23) : '-';
        console.log(`│ ${String(taskId).padStart(8)} │ ${String(slotNum).padStart(6)} │ ${data.status.padEnd(9)} │ ${claimedBy.padEnd(23)} │`);
      }
    }
    if (TOTAL_TASKS > 3) {
      console.log('│   ...    │  ...   │    ...    │          ...            │');
    }
    console.log('└──────────┴────────┴───────────┴─────────────────────────┘');

    console.log('\n✨ Initialization complete!');
    console.log('\nNext steps:');
    console.log('1. Verify in Firebase Console: https://console.firebase.google.com');
    console.log('2. Test slot claiming with concurrent requests');
    console.log('3. Monitor amt_task_slots collection during survey\n');

  } catch (error) {
    console.error('❌ Initialization failed:', error);
    throw error;
  }
}

// Run the script
initTaskSlots()
  .then(() => {
    console.log('🎉 Done!');
    process.exit(0);
  })
  .catch(error => {
    console.error('💥 Script failed:', error);
    process.exit(1);
  });
