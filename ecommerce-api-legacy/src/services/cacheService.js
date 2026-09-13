class CacheService {
    constructor() {
        this.store = new Map();
    }

    set(key, data) {
        this.store.set(key, data);
    }

    get(key) {
        return this.store.get(key);
    }
}

module.exports = new CacheService();
