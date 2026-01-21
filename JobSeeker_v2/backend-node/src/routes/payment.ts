import { Router } from 'express';
const router = Router();

router.post('/create-intent', (req, res) => res.send('Payment Intent'));

export default router;
