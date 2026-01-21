import { Router } from 'express';
const router = Router();

router.get('/google', (req, res) => res.send('Google Auth'));
router.get('/linkedin', (req, res) => res.send('LinkedIn Auth'));

export default router;
