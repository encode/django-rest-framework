/*!
 * Lunr languages, `Armenian` language
 * https://github.com/turbobit/lunr-languages
 *
 * Copyright 2021, Manikandan Venkatasubban
 * http://www.mozilla.org/MPL/
 */
/*!
 * based on
 * Snowball JavaScript Library v0.3
 * http://code.google.com/p/urim/
 * http://snowball.tartarus.org/
 *
 * Copyright 2010, Oleg Mazko
 * http://www.mozilla.org/MPL/
 */

/**
 * export the module via AMD, CommonJS or as a browser global
 * Export code from https://github.com/umdjs/umd/blob/master/returnExports.js
 */
;
(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD. Register as an anonymous module.
    define(factory)
  } else if (typeof exports === 'object') {
    /**
     * Node. Does not work with strict CommonJS, but
     * only CommonJS-like environments that support module.exports,
     * like Node.
     */
    module.exports = factory()
  } else {
    // Browser globals (root is window)
    factory()(root.lunr);
  }
}(this, function() {
  /**
   * Just return a value to define the module export.
   * This example returns an object, but the module
   * can return a function as the exported value.
   */
  return function(lunr) {
    /* throw error if lunr is not yet included */
    if ('undefined' === typeof lunr) {
      throw new Error('Lunr is not present. Please include / require Lunr before this script.');
    }

    /* throw error if lunr stemmer support is not yet included */
    if ('undefined' === typeof lunr.stemmerSupport) {
      throw new Error('Lunr stemmer support is not present. Please include / require Lunr stemmer support before this script.');
    }

    /* register specific locale function */
    lunr.hy = function() {
      this.pipeline.reset();
      this.pipeline.add(
        lunr.hy.trimmer,
        lunr.hy.stopWordFilter
      );
    };

    /* lunr trimmer function */
    // http://www.unicode.org/charts/
    lunr.hy.wordCharacters = "[" +
      "A-Za-z" +
      "\u0530-\u058F" + // armenian alphabet
      "\uFB00-\uFB4F" + // armenian ligatures
      "]";
    lunr.hy.trimmer = lunr.trimmerSupport.generateTrimmer(lunr.hy.wordCharacters);

    lunr.Pipeline.registerFunction(lunr.hy.trimmer, 'trimmer-hy');


    /* lunr stop word filter */
    // https://www.ranks.nl/stopwords/armenian
    lunr.hy.stopWordFilter = lunr.generateStopWordFilter('դու և եք էիր էիք հետո նաև նրանք որը վրա է որ պիտի են այս մեջ ն իր ու ի այդ որոնք այն կամ էր մի ես համար այլ իսկ էին ենք հետ ին թ էինք մենք նրա նա դուք եմ էի ըստ որպես ում'.split(' '));
    lunr.Pipeline.registerFunction(lunr.hy.stopWordFilter, 'stopWordFilter-hy');

    /* lunr stemmer function */
    lunr.hy.stemmer = (function() {

      return function(word) {
        // for lunr version 2
        if (typeof word.update === "function") {
          return word.update(function(word) {
            return word;
          })
        } else { // for lunr version <= 1
          return word;
        }

      }
    })();
    lunr.Pipeline.registerFunction(lunr.hy.stemmer, 'stemmer-hy');
  };
}))