import { readFileSync } from 'fs';
const s = JSON.parse(readFileSync('studios.json'));
const untagged = s.filter(x => !x.modalities || x.modalities.length === 0);
console.log('Untagged:', untagged.length, '/', s.length);
untagged.slice(0, 5).forEach(x => console.log(x.name, '|', x.address, '|', x.city));
